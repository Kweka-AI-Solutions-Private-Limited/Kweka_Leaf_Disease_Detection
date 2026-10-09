"""
leaf_disease_router.py — Phase 1 FastAPI Endpoint for Leaf Disease Analysis
-----------------------------------------------------------------------------
Orchestrates:
  1. Image Validation
  2. Crop / Plant Identification  (+ Gemini Vision fallback when UNCERTAIN)
  3. Primary Disease Detection    (+ Gemini Vision fallback when LOW confidence)
  4. Diagnosis Validation
  5. Response Formatting
  6. Multi-Tenant User Isolation via X-User-ID header context
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status, Depends, Query, Header
from pymongo.database import Database
from db.connection import get_db

from schemas.leaf_disease import LeafDiseaseAnalysisResponse
from services.leaf_disease.image_validator import validate_multiple_images
from services.leaf_disease.plant_identifier import identify_crop
from services.leaf_disease.disease_provider import get_disease_provider
from services.leaf_disease.diagnosis_validator import (
    validate_diagnosis_evidence,
    should_verify_with_gemini,
    reconcile_diagnoses,
)
from services.leaf_disease.gemini_leaf_fallback import gemini_identify_crop, gemini_analyze_disease
from services.leaf_disease.nacl_recommendation_engine import recommendation_engine

from db.activity_logger import log_activity, COLLECTION_NAME as ACTIVITY_LOGS_COLLECTION

INSPECTIONS_COLLECTION = "ldd_inspections"

router = APIRouter(prefix="/leaf-disease", tags=["Leaf Disease Analysis"])


def get_current_user_id(x_user_id: Optional[str] = Header(None, alias="X-User-ID")) -> str:
    """
    Extracts user_id context from the 'X-User-ID' HTTP request header.
    Defaults to 'default_user' if header is missing or empty.
    """
    if x_user_id and x_user_id.strip():
        return x_user_id.strip()
    return "default_user"


@router.get("/plants/search")
def search_plant_species(
    q: str = Query("", min_length=1, description="Plant name search query"),
    limit: int = Query(15, ge=1, le=30),
):
    """
    Dynamic plant/crop species search endpoint.
    Queries Pl@ntNet species API first, falls back to Gemini AI.
    Returns list of {value, label, scientific} dicts matching the query.
    """
    from services.leaf_disease.plant_search_service import search_plant_species as _search
    results = _search(query=q.strip(), limit=limit)
    return {"query": q, "results": results, "count": len(results)}


GEMINI_DISEASE_CONFIDENCE_THRESHOLD = 0.15


from bson import ObjectId

def _serialize_leaf_run(doc: dict) -> dict:
    """Helper to convert BSON ObjectId and datetime to string for FastAPI responses."""
    if not doc:
        return doc
    
    def _clean(val):
        if isinstance(val, ObjectId):
            return str(val)
        if isinstance(val, datetime):
            return val.isoformat()
        if isinstance(val, dict):
            return {k: _clean(v) for k, v in val.items()}
        if isinstance(val, list):
            return [_clean(v) for v in val]
        return val

    cleaned = _clean(doc)
    if isinstance(cleaned, dict) and "_id" in cleaned and "id" not in cleaned:
        cleaned["id"] = cleaned["_id"]
    return cleaned


@router.post("/analyze", response_model=LeafDiseaseAnalysisResponse)
async def analyze_leaf_disease(
    files: List[UploadFile] = File(...),
    selected_crop: Optional[str] = Form(None),
    db: Database = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Phase 1 Leaf Disease Analysis Endpoint.
    Accepts 1 to 5 leaf image files and optional crop selection override.
    Uses Gemini Vision as intelligent fallback when primary providers are uncertain.
    Persists analysis run history to MongoDB collection 'ldd_inspections' and logs to 'activity_logs', isolated by user_id.
    """
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one leaf image file must be uploaded."
        )

    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 images allowed per analysis request."
        )

    # Read image contents into memory
    file_tuples = []
    for upload_file in files:
        content = await upload_file.read()
        filename = upload_file.filename or "uploaded_leaf.jpg"
        file_tuples.append((filename, content))

    # 1. Image Validation
    validation_res = validate_multiple_images(file_tuples)

    analysis_id = f"LDA-{uuid.uuid4().hex[:8].upper()}"
    timestamp_str = datetime.now().isoformat()

    # Handle scenario where ALL images are invalid
    if not validation_res.is_any_valid:
        resp = LeafDiseaseAnalysisResponse(
            analysis_id=analysis_id,
            timestamp=timestamp_str,
            status="FAILED",
            validation=validation_res,
            crop=identify_crop(selected_crop=selected_crop),
            disease=None,
            diagnosis=None,
            retry_guidance="All submitted images failed validation. Please upload clear, uncorrupted images (JPEG, PNG, or WEBP) with adequate lighting.",
        )
        # Save failed run to history collection 'ldd_inspections' with user_id
        try:
            doc_data = resp.model_dump()
            doc_data["user_id"] = user_id
            doc_data["created_at"] = datetime.now(timezone.utc)
            doc_data["filenames"] = [f[0] for f in file_tuples]
            db[INSPECTIONS_COLLECTION].insert_one(doc_data)
        except Exception as e:
            print(f"[WARN] Failed to save leaf disease run history to '{INSPECTIONS_COLLECTION}': {e}")

        # Log activity to 'activity_logs' with user_id
        log_activity(
            db=db,
            action="LEAF_DISEASE_ANALYSIS",
            category="DIAGNOSIS",
            description=f"Leaf disease analysis failed for request '{analysis_id}': All submitted images failed quality validation.",
            status="FAILED",
            user_id=user_id,
            metadata={"analysis_id": analysis_id, "image_count": len(files)}
        )
        return resp

    # Filter details for usable valid images
    valid_details = [d for d in validation_res.details if d.is_valid]
    valid_filenames = [d.filename for d in valid_details]
    valid_raw_files = [(fn, fb) for fn, fb in file_tuples if any(fn == d.filename for d in valid_details)]

    # 2. Crop Identification
    crop_info = identify_crop(selected_crop=selected_crop, valid_filenames=valid_filenames)

    # 2b. Gemini Fallback: crop not identified by primary method
    if crop_info.status == "UNCERTAIN" and crop_info.crop_name == "Unknown":
        gemini_crop = gemini_identify_crop(raw_files=valid_raw_files)
        if gemini_crop is not None:
            crop_info = gemini_crop

    # 3. Primary Disease Detection Provider Call
    provider = get_disease_provider()
    disease_result = provider.detect_disease(
        crop_name=crop_info.crop_name,
        image_details=valid_details,
        raw_files=file_tuples
    )

    # 4. Preliminary Diagnosis Validation & Evidence Calibration
    diagnosis_res = validate_diagnosis_evidence(
        validation_result=validation_res,
        crop_info=crop_info,
        disease_result=disease_result
    )

    # 4b. Selective Gemini Second-Opinion Verification Layer
    if should_verify_with_gemini(disease_result, diagnosis_res):
        gemini_disease = gemini_analyze_disease(
            crop_name=crop_info.crop_name,
            raw_files=valid_raw_files
        )
        # Reconcile primary provider vs independent Gemini second opinion
        disease_result, diagnosis_res = reconcile_diagnoses(
            primary_result=disease_result,
            primary_val=diagnosis_res,
            gemini_result=gemini_disease
        )

    # Determine overall status & retry guidance
    if disease_result.provider_status == "PROVIDER_ERROR":
        analysis_status = "FAILED"
        retry_guidance = "Disease detection provider encountered an error. Please verify server configuration."
    elif diagnosis_res.is_uncertain:
        analysis_status = "UNCERTAIN"
        retry_guidance = diagnosis_res.targeted_close_up_request or "Diagnosis evidence is uncertain. Please upload a clear close-up of the leaf symptom."
    else:
        analysis_status = "SUCCESS"
        retry_guidance = None

    # 5. Treatment Recommendation Engine
    nacl_recs = None
    if disease_result and disease_result.disease_name:
        is_healthy_leaf = "healthy" in disease_result.disease_name.lower()
        nacl_recs = recommendation_engine.recommend_products(
            crop_name=crop_info.crop_name,
            disease_name=disease_result.disease_name,
            is_healthy=is_healthy_leaf,
            crop_compatibility_status=diagnosis_res.crop_compatibility_status,
            is_uncertain=diagnosis_res.is_uncertain,
            calibrated_confidence=diagnosis_res.calibrated_confidence,
            contradictory_evidence_found=diagnosis_res.contradictory_evidence_found,
            targeted_close_up_request=diagnosis_res.targeted_close_up_request,
            diagnosis_status=diagnosis_res.diagnosis_status
        )

    resp = LeafDiseaseAnalysisResponse(
        analysis_id=analysis_id,
        timestamp=timestamp_str,
        status=analysis_status,
        validation=validation_res,
        crop=crop_info,
        disease=disease_result,
        diagnosis=diagnosis_res,
        nacl_recommendations=nacl_recs,
        retry_guidance=retry_guidance,
    )

    # Save run record to MongoDB 'ldd_inspections' collection with user_id
    try:
        doc_data = resp.model_dump(mode="json")
        doc_data["user_id"] = user_id
        doc_data["created_at"] = datetime.now(timezone.utc)
        doc_data["filenames"] = [f[0] for f in file_tuples]
        db[INSPECTIONS_COLLECTION].insert_one(doc_data)
        print(f"[INFO] Saved leaf disease run '{analysis_id}' for user '{user_id}' to MongoDB collection '{INSPECTIONS_COLLECTION}'.")
    except Exception as e:
        print(f"[WARN] Failed to persist leaf disease run history to '{INSPECTIONS_COLLECTION}': {e}")

    # Log activity to 'activity_logs' collection with user_id
    disease_name_logged = disease_result.disease_name if disease_result else "Unknown"
    log_activity(
        db=db,
        action="LEAF_DISEASE_ANALYSIS",
        category="DIAGNOSIS",
        description=f"Executed leaf disease analysis '{analysis_id}' for crop '{crop_info.crop_name}' (Diagnosis: '{disease_name_logged}'). Status: '{analysis_status}'.",
        status=analysis_status,
        user_id=user_id,
        metadata={
            "analysis_id": analysis_id,
            "crop_name": crop_info.crop_name,
            "disease_name": disease_name_logged,
            "image_count": len(files),
            "calibrated_confidence": diagnosis_res.calibrated_confidence if diagnosis_res else None
        }
    )

    return resp


@router.get("/catalog")
def get_nacl_catalog(db: Database = Depends(get_db)):
    """
    Returns full NACL product catalog organized by category for interactive UI dropdown.
    """
    from db.nacl_product_db import get_all_nacl_products
    products = get_all_nacl_products(db)
    categorized: dict = {}
    for p in products:
        if "_id" in p:
            p["_id"] = str(p["_id"])
        cat = p.get("category", "Other Agrochemicals")
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(p)
    return {
        "total_count": len(products),
        "categories": categorized
    }


@router.post("/feedback")
def submit_leaf_disease_feedback(
    payload: dict,
    db: Database = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Stores user feedback on AI diagnosis to improve Gemini VLM prompt tuning and dataset validation.
    """
    if not payload:
        payload = {}
    payload["user_id"] = user_id
    payload["created_at"] = datetime.now(timezone.utc)
    res = db["ldd_feedback"].insert_one(payload)
    feedback_id = str(res.inserted_id)

    log_activity(
        db=db,
        action="SUBMIT_DIAGNOSIS_FEEDBACK",
        category="FEEDBACK",
        description=f"Submitted diagnostic feedback for analysis '{payload.get('analysis_id', 'N/A')}'.",
        status="SUCCESS",
        user_id=user_id,
        metadata={"feedback_id": feedback_id, "analysis_id": payload.get("analysis_id")}
    )

    return {"status": "success", "feedback_id": feedback_id, "message": "Feedback received successfully."}


@router.get("/history")
def get_leaf_disease_history(
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    crop_name: Optional[str] = Query(None),
    db: Database = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Returns list of historical Leaf Disease Analysis runs for requesting user ordered newest first from 'ldd_inspections'.
    Supports filtering by status ('SUCCESS', 'UNCERTAIN', 'FAILED') and crop_name.
    """
    query = {"user_id": user_id}
    if status:
        query["status"] = status.upper()
    if crop_name:
        query["crop.crop_name"] = crop_name

    cursor = db[INSPECTIONS_COLLECTION].find(query).sort("created_at", -1).limit(limit)
    runs = [_serialize_leaf_run(doc) for doc in cursor]
    return runs


@router.get("/history/{analysis_id}")
def get_leaf_disease_run(
    analysis_id: str,
    db: Database = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Retrieves a single historical Leaf Disease Analysis run by analysis_id for requesting user from 'ldd_inspections'.
    """
    query = {
        "$and": [
            {"$or": [{"analysis_id": analysis_id}, {"_id": analysis_id}]},
            {"user_id": user_id}
        ]
    }
    doc = db[INSPECTIONS_COLLECTION].find_one(query)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Leaf disease run with ID '{analysis_id}' not found.")
    return _serialize_leaf_run(doc)


@router.delete("/history/{analysis_id}")
def delete_leaf_disease_run(
    analysis_id: str,
    db: Database = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Deletes a specific Leaf Disease Analysis run record from history collection 'ldd_inspections' for requesting user.
    """
    query = {
        "$and": [
            {"$or": [{"analysis_id": analysis_id}, {"_id": analysis_id}]},
            {"user_id": user_id}
        ]
    }
    res = db[INSPECTIONS_COLLECTION].delete_one(query)
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Leaf disease run '{analysis_id}' not found.")

    log_activity(
        db=db,
        action="DELETE_ANALYSIS_RUN",
        category="HISTORY",
        description=f"Deleted leaf disease analysis run record '{analysis_id}'.",
        status="SUCCESS",
        user_id=user_id,
        metadata={"analysis_id": analysis_id}
    )

    return {"status": "deleted", "analysis_id": analysis_id}


@router.delete("/history")
def clear_leaf_disease_history(
    db: Database = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Clears all historical Leaf Disease Analysis runs belonging ONLY to requesting user from 'ldd_inspections'.
    """
    res = db[INSPECTIONS_COLLECTION].delete_many({"user_id": user_id})

    log_activity(
        db=db,
        action="CLEAR_ANALYSIS_HISTORY",
        category="HISTORY",
        description=f"Cleared all leaf disease analysis run history records ({res.deleted_count} records deleted).",
        status="SUCCESS",
        user_id=user_id,
        metadata={"deleted_count": res.deleted_count}
    )

    return {"status": "cleared", "deleted_count": res.deleted_count}


@router.get("/activity-logs")
def get_activity_logs(
    limit: int = Query(50, ge=1, le=200),
    category: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    user_id_param: Optional[str] = Query(None, alias="user_id"),
    db: Database = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Returns list of activity log entries for requesting user from the `activity_logs` collection, ordered newest first.
    """
    target_user_id = user_id_param if user_id_param else current_user_id
    query = {"user_id": target_user_id}
    if category:
        query["category"] = category.upper()
    if action:
        query["action"] = action.upper()

    cursor = db[ACTIVITY_LOGS_COLLECTION].find(query).sort("created_at", -1).limit(limit)
    logs = [_serialize_leaf_run(doc) for doc in cursor]
    return logs
