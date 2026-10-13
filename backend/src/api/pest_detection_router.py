"""
pest_detection_router.py — Phase 2 FastAPI Endpoint for Insect & Pest Detection
---------------------------------------------------------------------------------
Orchestrates:
  1. Image Validation (reusing shared local validator)
  2. Crop Identification & Normalization (optional user specification)
  3. Modular Pest Detection (IP102 local detector adapter)
  4. Diagnostic Validation & Strict >70% Confidence Gating
  5. Multi-Tenant User Isolation via X-User-ID header context
  6. Response Formatting and Inspection Logging
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status, Depends, Query, Header
from pymongo.database import Database
from db.connection import get_db

from schemas.leaf_disease import OverallImageValidationResult, CropIdentificationResult
from schemas.pest_detection import (
    PestDetectionAnalysisResponse,
    PestValidationResult,
    PestModelInfo,
    DetectedPestItem,
)
from services.leaf_disease.image_validator import validate_multiple_images
from services.leaf_disease.plant_identifier import identify_crop, normalize_crop_name
from services.pest_detection.pest_provider import get_pest_provider
from services.pest_detection.pest_validator import validate_pest_findings
from services.pest_detection.ip102_classes import get_supported_pest_classes, IP102_CATALOG
from db.activity_logger import log_activity

PEST_INSPECTIONS_COLLECTION = "pest_inspections"

router = APIRouter(prefix="/pest-detection", tags=["Insect & Pest Detection"])


from api.auth_router import get_current_user_id


@router.get("/status")
def get_pest_model_status():
    """Returns runtime readiness, checkpoint path, and architecture info."""
    provider = get_pest_provider()
    model_info = provider.get_model_info()
    return {
        "status": "online" if model_info.is_operational else "awaiting_weights",
        "model_info": model_info.model_dump(),
    }


@router.get("/classes")
def list_supported_pest_classes():
    """Lists all 102 recognized insect/pest classes in the IP102 benchmark catalog."""
    classes = get_supported_pest_classes()
    return {
        "count": len(classes),
        "dataset": "IP102 Benchmark Insect Dataset",
        "classes": classes,
    }


@router.post("/analyze", response_model=PestDetectionAnalysisResponse)
async def analyze_insect_pests(
    files: List[UploadFile] = File(...),
    selected_crop: Optional[str] = Form(None),
    db: Database = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Phase 2 Insect & Pest Detection Endpoint.
    Analyzes uploaded leaf/plant images for insect specimens and feeding damage patterns.
    Enforces strict >70% confidence threshold gating and multi-tenant data isolation.
    """
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 1 image file is required.",
        )

    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 images allowed per inspection.",
        )

    # 1. Read files into memory
    file_payloads: List[tuple[str, bytes]] = []
    for f in files:
        content = await f.read()
        file_payloads.append((f.filename or "upload.jpg", content))

    # 2. Local Image Quality Validation
    val_result: OverallImageValidationResult = validate_multiple_images(file_payloads)
    if not val_result.is_any_valid:
        first_err = "No valid image uploaded."
        for d in val_result.details:
            if d.errors:
                first_err = d.errors[0]
                break
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image validation failed: {first_err}",
        )

    # 3. Crop Identification (Optional)
    if selected_crop and selected_crop.strip():
        crop_info = identify_crop(selected_crop=selected_crop.strip())
    else:
        crop_info = CropIdentificationResult(
            crop_name="Unspecified",
            source="unspecified",
            status="NOT_SPECIFIED",
            evidence_note="Host crop not specified by user; analyzed across all crop susceptibilities.",
        )

    # 4. Modular Pest Detection
    provider = get_pest_provider()
    model_info = provider.get_model_info()

    # Get bytes of first valid image
    first_valid_idx = next(i for i, d in enumerate(val_result.details) if d.is_valid)
    target_filename, target_bytes = file_payloads[first_valid_idx]
    target_detail = val_result.details[first_valid_idx]

    detected_pests, updated_model_info = provider.detect_pests(
        image_bytes=target_bytes,
        crop_name=crop_info.crop_name,
        image_detail=target_detail,
    )

    # 5. Diagnostic Validation & Strict >70% Confidence Gating
    validation_eval = validate_pest_findings(
        detections=detected_pests,
        crop_info=crop_info,
        validation_result=val_result,
        model_info=updated_model_info,
    )

    primary_pest = None
    if detected_pests:
        sorted_pests = sorted(detected_pests, key=lambda p: p.confidence, reverse=True)
        primary_pest = sorted_pests[0]

    # Map overall response status
    if not updated_model_info.is_operational:
        overall_status = "MODEL_UNAVAILABLE"
    elif not detected_pests:
        overall_status = "NO_PEST_DETECTED"
    elif validation_eval.is_uncertain:
        overall_status = "UNCERTAIN"
    else:
        overall_status = "SUCCESS"

    analysis_id = str(uuid.uuid4())
    timestamp_str = datetime.now(timezone.utc).isoformat()

    response = PestDetectionAnalysisResponse(
        analysis_id=analysis_id,
        timestamp=timestamp_str,
        status=overall_status,
        crop=crop_info,
        validation=val_result,
        model_info=updated_model_info,
        detected_pests=detected_pests,
        primary_pest=primary_pest,
        validation_result=validation_eval,
        phase_notice="Phase 2: Insect & Pest Detection (Isolated Experimental Pipeline)",
    )

    # 6. MongoDB Persistence with Multi-Tenant Isolation
    try:
        inspection_doc = {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc),
            "status": overall_status,
            "crop": crop_info.model_dump(),
            "model_info": updated_model_info.model_dump(),
            "detected_pests": [p.model_dump() for p in detected_pests],
            "primary_pest": primary_pest.model_dump() if primary_pest else None,
            "validation_result": validation_eval.model_dump(),
        }
        db[PEST_INSPECTIONS_COLLECTION].insert_one(inspection_doc)

        log_activity(
            db=db,
            action="pest_detection_run",
            category="INSPECTION",
            description=f"Pest inspection completed with status {overall_status}",
            status="SUCCESS" if overall_status in ("SUCCESS", "UNCERTAIN") else overall_status,
            user_id=user_id,
            metadata={
                "analysis_id": analysis_id,
                "status": overall_status,
                "primary_pest": primary_pest.pest_name if primary_pest else None,
                "confidence": primary_pest.confidence if primary_pest else 0.0,
                "crop": crop_info.crop_name,
            },
        )
    except Exception as e:
        # Non-fatal logging error
        print(f"[WARN] Failed to persist pest inspection record to DB: {e}")

    return response
