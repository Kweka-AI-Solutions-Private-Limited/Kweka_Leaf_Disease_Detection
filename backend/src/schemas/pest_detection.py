"""
pest_detection.py — Pydantic Schemas for Phase 2: Insect & Pest Detection
--------------------------------------------------------------------------
Defines standardized data contracts for:
  - Localized insect/pest detections (bounding boxes, confidence, class ID)
  - Distinction between direct pest specimens vs. visible foliar/stem damage
  - Model availability, architecture metadata, and checkpoint status
  - Strict >70% confidence gating and calibrated uncertainty validation
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from schemas.leaf_disease import OverallImageValidationResult, CropIdentificationResult


class PestBoundingBox(BaseModel):
    """Normalized bounding box coordinates [0.0 - 1.0]."""
    ymin: float = Field(..., ge=0.0, le=1.0, description="Normalized top coordinate")
    xmin: float = Field(..., ge=0.0, le=1.0, description="Normalized left coordinate")
    ymax: float = Field(..., ge=0.0, le=1.0, description="Normalized bottom coordinate")
    xmax: float = Field(..., ge=0.0, le=1.0, description="Normalized right coordinate")
    label: Optional[str] = Field(None, description="Class label for this detection")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Localization confidence")


class DetectedPestItem(BaseModel):
    """Structured detection record for a single insect or visible damage instance."""
    pest_name: str = Field(..., description="Common vernacular name of insect or pest")
    scientific_name: Optional[str] = Field(None, description="Binomial taxonomic name")
    pest_class_id: int = Field(..., description="Canonical integer class ID (e.g. from IP102)")
    category: str = Field(
        ...,
        description="Category classification: 'INSECT', 'LARVA', 'NYMPH', 'ADULT', or 'PEST_DAMAGE'"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Raw model confidence score")
    bounding_box: Optional[PestBoundingBox] = Field(
        None,
        description="Bounding box coordinates if localization is supported"
    )
    damage_type: Optional[str] = Field(
        None,
        description="Damage manifestation (e.g., foliar_chewing, stem_boring, sap_sucking, mining)"
    )
    description: Optional[str] = Field(None, description="Brief biological profile or symptom description")
    affected_organs: List[str] = Field(default_factory=list, description="Plant parts commonly affected")


class PestModelInfo(BaseModel):
    """Metadata regarding the registered pest detection model and inference runtime."""
    model_id: str = Field(..., description="Identifier of the model/pipeline")
    model_name: str = Field(..., description="Human-readable model name")
    architecture: str = Field(..., description="Neural network architecture family")
    is_operational: bool = Field(..., description="True if weights are loaded and ready for inference")
    checkpoint_path: Optional[str] = Field(None, description="Filesystem path where weights are loaded or expected")
    supported_classes_count: int = Field(102, description="Number of recognized pest classes in catalog")
    framework: str = Field("PyTorch / ONNX", description="Underlying inference runtime framework")
    license: str = Field("Apache-2.0 / Academic Research", description="Model weights usage license")
    status_message: str = Field(..., description="Operational status or explanation if unavailable")


class PestValidationResult(BaseModel):
    """Diagnostic validation and strict confidence gate results for pest detections."""
    diagnosis_status: str = Field(
        ...,
        description="CONFIRMED | UNCERTAIN | UNSUPPORTED | NO_PEST_DETECTED | MODEL_UNAVAILABLE"
    )
    calibrated_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calibrated confidence score penalizing image flaws or ambiguities"
    )
    is_uncertain: bool = Field(
        ...,
        description="True if calibrated confidence <= 0.70 or validation rules fail"
    )
    confidence_gate_passed: bool = Field(
        ...,
        description="True strictly when confidence > 0.70; false for <= 0.70"
    )
    evidence_level: str = Field(
        "LOW",
        description="EVIDENCE level: 'HIGH', 'MEDIUM', 'LOW', or 'INSUFFICIENT'"
    )
    pest_type_distinction: str = Field(
        "UNCERTAIN",
        description="Distinction: 'SPECIMEN_DETECTED', 'DAMAGE_ONLY', 'MIXED', or 'UNCERTAIN'"
    )
    crop_host_compatibility: str = Field(
        "UNRESTRICTED",
        description="Crop compatibility: 'COMPATIBLE', 'POTENTIAL_MISMATCH', 'UNRESTRICTED', 'UNKNOWN_CROP'"
    )
    image_quality_status: str = Field("ACCEPTABLE", description="Image quality: GOOD, ACCEPTABLE, SUBOPTIMAL, POOR")
    validation_notes: List[str] = Field(default_factory=list, description="Reasoning and audit trail notes")
    retry_guidance: Optional[str] = Field(
        None,
        description="Actionable user instructions for re-photographing when uncertain"
    )


class PestDetectionAnalysisResponse(BaseModel):
    """Standardized top-level response payload for pest detection endpoint."""
    analysis_id: str = Field(..., description="Unique UUID for this analysis session")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    status: str = Field(
        ...,
        description="Overall status: SUCCESS | UNCERTAIN | UNSUPPORTED | NO_PEST_DETECTED | MODEL_UNAVAILABLE | FAILED"
    )
    crop: CropIdentificationResult = Field(..., description="Crop identity and normalization metadata")
    validation: OverallImageValidationResult = Field(..., description="Image quality validation result")
    model_info: PestModelInfo = Field(..., description="Model and checkpoint status")
    detected_pests: List[DetectedPestItem] = Field(default_factory=list, description="List of detected pests/damage")
    primary_pest: Optional[DetectedPestItem] = Field(None, description="Primary detected pest with highest confidence")
    validation_result: PestValidationResult = Field(..., description="Validation and strict gate evaluation")
    phase_notice: str = Field(
        "Phase 2: Insect & Pest Detection (Isolated Experimental Pipeline)",
        description="Pipeline phase identification notice"
    )
