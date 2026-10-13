"""
unified_test.py — Pydantic Schemas for Standalone Unified Testing Interface
----------------------------------------------------------------------------
Defines data structures for testing:
  1. Crop Identification (Pl@ntNet live species identification)
  2. Disease Detection (Pl@ntNet EPPO live pathology with strict >70% confidence gating)
  3. Weed Detection (Local model adapter — honest degraded status when weights absent)
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

from schemas.leaf_disease import ImageValidationDetail


class CropIdentificationTestResult(BaseModel):
    """Output for Crop/Botanical Species Identification."""
    status: Literal["CONFIRMED", "UNCERTAIN", "SUSPECTED", "NEEDS_VERIFICATION", "UNSUPPORTED", "MODEL_UNAVAILABLE", "ERROR"]
    crop_name: str
    scientific_name: Optional[str] = None
    common_names: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    is_agricultural_crop: bool = True
    plant_type: Optional[str] = None
    quality_warning: Optional[str] = None
    provider: str
    is_operational: bool
    message: str


class DiseaseCandidateTestItem(BaseModel):
    disease_name: str
    confidence: Optional[float] = None


class DiseaseDetectionTestResult(BaseModel):
    """Output for Plant Pathology / Disease Detection."""
    status: Literal["CONFIRMED", "UNCERTAIN", "SUSPECTED", "NEEDS_VERIFICATION", "NO_DISEASE_DETECTED", "INVALID_CATEGORY", "MODEL_UNAVAILABLE", "ERROR"]
    disease_name: str
    common_name: Optional[str] = None
    scientific_name: Optional[str] = None
    confidence: Optional[float] = None
    confidence_gate_passed: bool = False
    provider: str
    is_operational: bool
    candidates: List[DiseaseCandidateTestItem] = Field(default_factory=list)
    message: str
    raw_provider_finding: Optional[str] = None
    raw_provider_score: Optional[float] = None
    category_warning: Optional[str] = None
    host_crop_compatibility: Optional[str] = None


class WeedBoundingBox(BaseModel):
    ymin: float = Field(ge=0.0, le=1.0)
    xmin: float = Field(ge=0.0, le=1.0)
    ymax: float = Field(ge=0.0, le=1.0)
    xmax: float = Field(ge=0.0, le=1.0)
    label: str
    confidence: float = Field(ge=0.0, le=1.0)


class DetectedWeedTestItem(BaseModel):
    weed_name: str
    scientific_name: Optional[str] = None
    confidence: float
    bounding_box: Optional[WeedBoundingBox] = None
    detection_type: Optional[str] = None
    growth_habit: Optional[str] = None


class WeedDetectionTestResult(BaseModel):
    """Output for Weed Detection."""
    status: Literal["CONFIRMED", "UNCERTAIN", "NO_WEED_DETECTED", "MODEL_UNAVAILABLE", "ERROR"]
    detected_weeds: List[DetectedWeedTestItem] = Field(default_factory=list)
    confidence: Optional[float] = None
    provider: str
    is_operational: bool
    model_name: Optional[str] = None
    architecture_type: Optional[str] = None
    supports_bounding_boxes: bool = False
    dataset_origin: Optional[str] = None
    message: str


class PestBoundingBoxTestItem(BaseModel):
    ymin: float = Field(ge=0.0, le=1.0)
    xmin: float = Field(ge=0.0, le=1.0)
    ymax: float = Field(ge=0.0, le=1.0)
    xmax: float = Field(ge=0.0, le=1.0)
    label: str
    confidence: float = Field(ge=0.0, le=1.0)


class DetectedPestTestItem(BaseModel):
    pest_name: str
    scientific_name: Optional[str] = None
    pest_class_id: int
    category: str
    confidence: float
    damage_type: Optional[str] = None
    bounding_box: Optional[PestBoundingBoxTestItem] = None


class PestDetectionTestResult(BaseModel):
    """Output for Insect & Pest Detection (IP102 benchmark model with Hybrid Consensus)."""
    status: Literal["CONFIRMED", "UNCERTAIN", "SUSPECTED", "NEEDS_VERIFICATION", "NO_PEST_DETECTED", "MODEL_UNAVAILABLE", "ERROR"]
    detected_pests: List[DetectedPestTestItem] = Field(default_factory=list)
    primary_pest: Optional[str] = None
    confidence: Optional[float] = None
    confidence_gate_passed: bool = False
    provider: str
    is_operational: bool
    model_name: str
    supported_classes_count: int = 102
    consensus_applied: bool = False
    cross_model_verified: bool = False
    validation_source: Optional[str] = None
    original_local_confidence: Optional[float] = None
    message: str



class DetectorStatusItem(BaseModel):
    detector_name: str
    provider: str
    is_operational: bool
    status: Literal["OPERATIONAL", "UNAVAILABLE", "AWAITING_WEIGHTS"]
    type: str
    details: str


class UnifiedTestStatusResponse(BaseModel):
    detectors: Dict[str, DetectorStatusItem]


from schemas.cross_validation import CrossValidationResult


class UnifiedTestAnalysisResponse(BaseModel):
    analysis_id: str
    timestamp: str
    image_validation: ImageValidationDetail
    crop: CropIdentificationTestResult
    disease: DiseaseDetectionTestResult
    weed: WeedDetectionTestResult
    pest: Optional[PestDetectionTestResult] = None
    cross_validation: Optional[CrossValidationResult] = None
    notes: List[str] = Field(default_factory=list)

