"""
leaf_disease.py — Schemas for Leaf Disease Analysis (Phase 1)
------------------------------------------------------------
Defines strict Pydantic schemas for image validation, crop identification,
normalized disease detection provider responses, diagnosis validation,
and final API payload structures.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from schemas.nacl_catalog import ProductRecommendationResult


class ImageValidationDetail(BaseModel):
    filename: str
    is_valid: bool
    format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: int = 0
    blur_score: float = 0.0
    brightness: float = 0.0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class OverallImageValidationResult(BaseModel):
    total_submitted: int
    valid_count: int
    invalid_count: int
    is_any_valid: bool
    details: List[ImageValidationDetail] = Field(default_factory=list)


class CropIdentificationResult(BaseModel):
    crop_name: str
    confidence: Optional[float] = None
    source: str = Field(description="'user_selected', 'automatic', or 'uncertain'")
    status: str = Field(description="'CONFIRMED', 'USER_SPECIFIED', or 'UNCERTAIN'")
    evidence_note: str


class VisualEvidenceDetail(BaseModel):
    directly_visible: List[str] = Field(default_factory=list, description="Directly observable features: lesion color/shape, cottony/waxy structures, webbing, etc.")
    inferred: List[str] = Field(default_factory=list, description="Features inferred from symptoms")
    unavailable: List[str] = Field(default_factory=list, description="Key diagnostic evidence missing due to distance/blur/angle")
    dominant_morphology: str = Field(default="UNSPECIFIED", description="Primary visual symptom structure observed")


class DiseaseCandidate(BaseModel):
    disease_name: str
    category: str = Field(default="UNKNOWN_UNCERTAIN", description="FUNGAL, BACTERIAL, VIRAL, PEST_INSECT, NUTRIENT_PHYSIOLOGICAL, UNKNOWN_UNCERTAIN")
    confidence: Optional[float] = None
    evidence_match_score: Optional[float] = None


class NormalizedDiseaseResult(BaseModel):
    disease_name: str
    category: str = Field(default="UNKNOWN_UNCERTAIN", description="Primary diagnostic category: FUNGAL, BACTERIAL, VIRAL, PEST_INSECT, NUTRIENT_PHYSIOLOGICAL, UNKNOWN_UNCERTAIN")
    confidence: Optional[float] = None
    calibrated_confidence: Optional[float] = None
    provider_name: str
    is_mock: bool = False
    supported: bool = True
    candidates: List[DiseaseCandidate] = Field(default_factory=list)
    visual_evidence: Optional[VisualEvidenceDetail] = None
    provider_status: str = Field(description="'OK', 'UNSUPPORTED_CROP', 'LOW_CONFIDENCE', 'PROVIDER_ERROR', 'MOCK'")
    error_message: Optional[str] = None


class DiagnosisValidationResult(BaseModel):
    evidence_level: str = Field(description="'HIGH', 'MEDIUM', or 'LOW'")
    image_quality_status: str
    crop_compatibility_status: str
    consistency_status: str
    is_uncertain: bool
    calibrated_confidence: float = 0.0
    contradictory_evidence_found: bool = False
    targeted_close_up_request: Optional[str] = None
    diagnosis_status: str = Field(default="CONFIRMED", description="'CONFIRMED', 'CONFIRMED_BY_SECOND_OPINION', 'UNCERTAIN', or 'CONFLICTING'")
    primary_diagnosis: Optional[str] = Field(None, description="Primary provider reported diagnosis")
    primary_confidence: Optional[float] = Field(None, description="Primary provider reported raw confidence")
    gemini_verification: str = Field(default="NOT_REQUIRED", description="'NOT_REQUIRED', 'AGREED', 'DISAGREED', or 'UNCERTAIN'")
    validation_notes: List[str] = Field(default_factory=list)


class LeafDiseaseAnalysisResponse(BaseModel):
    analysis_id: str
    timestamp: str
    status: str = Field(description="'SUCCESS', 'UNCERTAIN', or 'FAILED'")
    validation: OverallImageValidationResult
    crop: CropIdentificationResult
    disease: Optional[NormalizedDiseaseResult] = None
    diagnosis: Optional[DiagnosisValidationResult] = None
    nacl_recommendations: Optional[ProductRecommendationResult] = None
    retry_guidance: Optional[str] = None
    phase_notice: str = "Phase 3: Evidence-First Calibrated Leaf Disease & Pest Analysis with NACL Safety Gate."

