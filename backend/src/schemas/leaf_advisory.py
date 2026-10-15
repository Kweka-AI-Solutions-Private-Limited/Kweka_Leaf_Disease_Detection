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
    Includes core mandatory intake (Location, Season, Growth Stage, Onset, Weather, Previous Treatment)
    and optional extended agronomy context (Acreage, Sowing Date, Variety, Plant Parts, Irrigation, Notes).
    """
    analysis_id: Optional[str] = None
    crop_name: str
    disease_name: Optional[str] = None
    pest_name: Optional[str] = None
    geolocation: Optional[str] = None  # Regional context (e.g., Punjab, Uttar Pradesh)
    season: Optional[str] = None       # Seasonal context (e.g., Kharif, Rabi, Zaid)
    image_url: Optional[str] = None    # Specimen image preserved from diagnosis

    # Core Intake Parameters
    growth_stage: Optional[str] = None       # Seedling, Vegetative, Flowering, Fruiting / Maturation
    onset_days: Optional[str] = None         # 1-2 days ago (Acute), 3-7 days ago, >1 week ago
    recent_weather: Optional[str] = None     # Clear & Dry, Rainy / High Humidity, High Heat, Overcast / Windy
    previous_treatment: Optional[str] = None # None (First Spray), Already Sprayed - Ineffective, Rotational Spray

    # Optional Extended Agronomy Parameters
    area_sown: Optional[float] = None        # e.g., 2.5
    area_unit: Optional[str] = "acres"       # "acres" or "hectares"
    sowing_date: Optional[str] = None        # e.g. "2026-08-15"
    crop_variety: Optional[str] = None       # e.g. "BT Cotton", "US-7067"
    plant_part_affected: Optional[List[str]] = None  # e.g. ["Leaf", "Stem"]
    irrigation_condition: Optional[str] = None       # Normal, Waterlogged / Flooded, Drought Stressed
    severity_level: Optional[str] = None     # Mild (<10%), Moderate (10-30%), Severe (>30%)
    farmer_name: Optional[str] = None
    farmer_phone: Optional[str] = None
    farmer_notes: Optional[str] = None
    gps_coordinates: Optional[str] = None


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
    intake_summary: Optional[Dict[str, Any]] = None  # Structured farmer telemetry record
    area_calculation_summary: Optional[str] = None    # Summary of total bottle & tank calculations for acreage
    escalation_required: bool = False
    escalation_reason: Optional[str] = None
    combination_guidance: Optional[str] = None        # Scientifically verified tank-mix / combination advice
    safety_disclaimer: str = (
        "Advisory recommendations are generated based on identified foliar conditions, optional regional "
        "and seasonal climate inputs, and verified NACL product registrations. Follow statutory product label "
        "guidelines and local agronomist counsel prior to chemical application."
    )

