"""
leaf_advisory_router.py — FastAPI Router for Leaf Advisory & Agronomic Intelligence
------------------------------------------------------------------------------------
Endpoints:
  - GET  /api/leaf-advisory/history : Retrieve historical diagnoses from database
  - GET  /api/leaf-advisory/options : Regional and seasonal quick-pick options
  - POST /api/leaf-advisory/generate: Generate tailored agronomist advisory with Gemini & NACL
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pymongo.database import Database

from db.connection import get_db
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
    db: Database = Depends(get_db)
):
    """
    Generates personalized agronomist advisory taking into account the crop,
    diagnosed condition, optional geolocation, and optional season.
    """
    if not request.crop_name or not request.crop_name.strip():
        raise HTTPException(status_code=400, detail="Crop name is required to generate an advisory.")

    service = LeafAdvisoryService(db=db)
    try:
        return service.generate_advisory(request)
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to generate agronomist advisory: {str(ex)}")
