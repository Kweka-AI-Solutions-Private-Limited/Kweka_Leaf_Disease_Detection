"""
leaf_advisory_router.py — FastAPI Router for Leaf Advisory & Agronomic Intelligence
------------------------------------------------------------------------------------
Endpoints:
  - GET  /api/leaf-advisory/history : Retrieve historical diagnoses from database
  - GET  /api/leaf-advisory/options : Regional and seasonal quick-pick options
  - POST /api/leaf-advisory/generate: Generate tailored agronomist advisory with Gemini & NACL
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pymongo.database import Database

from db.connection import get_db
from db.activity_logger import log_activity
from api.leaf_disease_router import get_current_user_id
from schemas.leaf_advisory import (
    AdvisoryHistoricalDiagnosisItem,
    LeafAdvisoryRequest,
    LeafAdvisoryResponse
)
from services.leaf_advisory.leaf_advisory_service import LeafAdvisoryService

router = APIRouter(prefix="/leaf-advisory", tags=["Leaf Advisory"])


@router.get("/history", response_model=List[AdvisoryHistoricalDiagnosisItem])
def get_advisory_history(
    limit: int = Query(50, ge=1, le=100),
    db: Database = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Returns recent historical diagnoses from previous scans for advisory selection.
    """
    service = LeafAdvisoryService(db=db)
    return service.get_historical_diagnoses(user_id=user_id, limit=limit)


@router.get("/options")
def get_advisory_options():
    """
    Returns curated lists of agricultural regions and seasons for UI quick selection.
    Both remain strictly optional for user input.
    """
    return {
        "suggested_regions": [
            "Punjab (North Indus Plain)",
            "Haryana (North Western Zone)",
            "Uttar Pradesh (Indo-Gangetic Basin)",
            "Maharashtra (Deccan Plateau)",
            "Karnataka (Southern Plateau)",
            "Andhra Pradesh & Telangana (Krishna-Godavari Zone)",
            "Gujarat (Western Semi-Arid)",
            "Madhya Pradesh (Central Plateau)",
            "Tamil Nadu (Southern Coastal/Plains)",
            "West Bengal (Lower Gangetic Plain)",
            "Rajasthan (Arid Western Zone)",
            "Bihar (Middle Gangetic Plain)"
        ],
        "suggested_seasons": [
            {
                "name": "Kharif (Monsoon / Autumn)",
                "description": "June to October — High humidity, heavy precipitation, elevated foliar disease pressure."
            },
            {
                "name": "Rabi (Winter / Spring)",
                "description": "October to March — Cooler temperatures, morning dew, powdery mildews and rusts prevalent."
            },
            {
                "name": "Zaid (Summer / Pre-Monsoon)",
                "description": "March to June — Warm and dry conditions, high evapotranspiration, sap-sucking pest proliferation."
            },
            {
                "name": "Spring / Transitional",
                "description": "Moderate temperatures, vegetative growth flush, early pest colonization."
            },
            {
                "name": "Autumn / Post-Monsoon",
                "description": "Declining rainfall, maturing crops, late blight and secondary rots."
            }
        ]
    }


@router.post("/generate", response_model=LeafAdvisoryResponse)
def generate_advisory(
    request: LeafAdvisoryRequest,
    db: Database = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Generates personalized agronomist advisory taking into account the crop,
    diagnosed condition, optional geolocation, and optional season.
    Persists advisory report isolated by user_id and logs to activity_logs.
    """
    if not request.crop_name or not request.crop_name.strip():
        raise HTTPException(status_code=400, detail="Crop name is required to generate an advisory.")

    service = LeafAdvisoryService(db=db)
    try:
        result = service.generate_advisory(request)

        # Resolve and sanitize persistent specimen image
        final_img = result.image_url
        if final_img and isinstance(final_img, str) and final_img.startswith("blob:"):
            final_img = None
        if not final_img and request.image_url and isinstance(request.image_url, str) and not request.image_url.startswith("blob:"):
            final_img = request.image_url
        if not final_img and request.analysis_id:
            try:
                pdoc = db["ldd_inspections"].find_one({
                    "$or": [{"analysis_id": request.analysis_id}, {"_id": request.analysis_id}]
                })
                if pdoc:
                    p_img = pdoc.get("image_url") or pdoc.get("thumbnail")
                    if p_img and isinstance(p_img, str) and not p_img.startswith("blob:"):
                        final_img = p_img
            except Exception:
                pass

        # 1. Persist to user-isolated collection 'ldd_advisories'
        adv_doc = result.model_dump(mode="json")
        adv_doc["image_url"] = final_img
        adv_doc["user_id"] = user_id
        adv_doc["created_at"] = datetime.now(timezone.utc)
        try:
            db["ldd_advisories"].insert_one(adv_doc.copy())
        except Exception as e:
            print(f"[WARN] Failed to persist advisory to ldd_advisories: {e}")

        # 1b. Persist as an inspection history record in 'ldd_inspections' for History timeline
        try:
            history_entry = {
                "analysis_id": result.advisory_id,
                "source": "LEAF_ADVISORY",
                "status": "SUCCESS",
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "timestamp": result.timestamp,
                "crop": {
                    "crop_name": result.crop_name,
                    "status": "CONFIRMED"
                },
                "disease": {
                    "disease_name": result.disease_name or "None",
                    "status": "CONFIRMED" if result.disease_name else "NOT_DETECTED"
                } if result.disease_name else None,
                "pest": {
                    "primary_pest": result.pest_name or "No pest detected",
                    "status": "CONFIRMED" if result.pest_name else "NO_PEST_DETECTED"
                } if result.pest_name else None,
                "geolocation": result.geolocation,
                "season": result.season,
                "seasonal_risk": result.seasonal_risk.model_dump() if result.seasonal_risk else None,
                "advisory": adv_doc,
                "nacl_products": [p.model_dump() for p in result.nacl_products],
                "cultural_remedies": result.cultural_remedies,
                "chemical_management": result.chemical_management,
                "ai_advisory_summary": result.ai_advisory_summary,
                "image_url": final_img,
                "parent_analysis_id": request.analysis_id
            }
            db["ldd_inspections"].insert_one(history_entry)
        except Exception as e:
            print(f"[WARN] Failed to persist advisory history entry to ldd_inspections: {e}")

        # 1c. If requested for a specific prior inspection analysis_id, link advisory directly to it
        if request.analysis_id:
            try:
                db["ldd_inspections"].update_one(
                    {
                        "$and": [
                            {"$or": [{"analysis_id": request.analysis_id}, {"_id": request.analysis_id}]},
                            {"user_id": user_id}
                        ]
                    },
                    {
                        "$set": {
                            "advisory": adv_doc,
                            "advisory_id": result.advisory_id,
                            "has_advisory": True
                        }
                    }
                )
            except Exception as e:
                print(f"[WARN] Failed to link advisory to inspection '{request.analysis_id}': {e}")

        # 2. Log activity with user_id context
        condition_label = request.disease_name or request.pest_name or "General Health"
        log_activity(
            db=db,
            action="GENERATE_LEAF_ADVISORY",
            category="ADVISORY",
            description=f"Generated agronomist advisory for {request.crop_name} ({condition_label}).",
            status="SUCCESS",
            user_id=user_id,
            metadata={
                "advisory_id": result.advisory_id,
                "crop_name": request.crop_name,
                "disease_name": request.disease_name,
                "pest_name": request.pest_name,
                "geolocation": request.geolocation,
                "season": request.season,
                "nacl_products_count": len(result.nacl_products)
            }
        )

        return result
    except Exception as ex:
        # Log failure
        try:
            log_activity(
                db=db,
                action="GENERATE_LEAF_ADVISORY",
                category="ADVISORY",
                description=f"Advisory generation failed for {request.crop_name}: {str(ex)}",
                status="FAILED",
                user_id=user_id,
                metadata={"crop_name": request.crop_name, "error": str(ex)}
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to generate agronomist advisory: {str(ex)}")
