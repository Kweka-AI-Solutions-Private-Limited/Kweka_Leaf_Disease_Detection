"""
leaf_advisory.py — Schemas for Leaf Advisory & Agronomic Intelligence Service
-----------------------------------------------------------------------------
Defines data models for:
  1. Historical diagnosis selection
  2. Optional Geolocation & Season contextual requests
  3. Tailored agronomist advisory recommendations backed by NACL Catalog & Gemini
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from schemas.nacl_catalog import NACLProductRecommendation


class AdvisoryHistoricalDiagnosisItem(BaseModel):
    """Normalized diagnostic history item selectable by the user."""
    analysis_id: str
    source: str = "LEAF_SCANNER"  # "LEAF_SCANNER" or "LEAF_DIAGNOSIS"
    timestamp: str
    crop_name: str
    disease_name: Optional[str] = None
    pest_name: Optional[str] = None
    status: str
    confidence: Optional[float] = None
    summary: Optional[str] = None
    image_url: Optional[str] = None


class LeafAdvisoryRequest(BaseModel):
    """
    Request payload to generate personalized agronomic advisory.
    geolocation and season are OPTIONAL.
    """
    analysis_id: Optional[str] = None
    crop_name: str
    disease_name: Optional[str] = None
    pest_name: Optional[str] = None
    geolocation: Optional[str] = None  # Optional regional context (e.g., Punjab, Maharashtra)
    season: Optional[str] = None       # Optional seasonal context (e.g., Kharif, Rabi, Zaid)
    image_url: Optional[str] = None    # Specimen image preserved from diagnosis


class SeasonalRiskAssessment(BaseModel):
    """Regional & seasonal climate risk analysis synthesized by Gemini."""
    season_name: str = "General / All Season"
    geolocation_name: str = "General Agricultural Region"
    climate_factors: str
    disease_pressure_level: str = "MODERATE"  # "HIGH", "MODERATE", "LOW", "VARIABLE"
    weather_spray_window_advice: str


class LeafAdvisoryResponse(BaseModel):
    """Comprehensive agronomist advisory response."""
    advisory_id: str
    timestamp: str
    crop_name: str
    disease_name: Optional[str] = None
    pest_name: Optional[str] = None
    geolocation: Optional[str] = None
    season: Optional[str] = None
    seasonal_risk: SeasonalRiskAssessment
    nacl_products: List[NACLProductRecommendation] = Field(default_factory=list)
    ai_advisory_summary: str
    cultural_remedies: List[str] = Field(default_factory=list)
    chemical_management: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    safety_disclaimer: str = (
        "Advisory recommendations are generated based on identified foliar conditions, optional regional "
        "and seasonal climate inputs, and verified NACL product registrations. Follow statutory product label "
        "guidelines and local agronomist counsel prior to chemical application."
    )
