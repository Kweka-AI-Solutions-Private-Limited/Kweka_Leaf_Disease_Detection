"""
weed_detection.py — Pydantic Schemas for Phase 3: Weed Detection
-----------------------------------------------------------------
Defines standardized data contracts for:
  - Localized weed detections (bounding boxes, confidence, class ID)
  - Whole-image weed classification vs. multi-object detection distinction
  - Canonical taxonomy mapping (DeepWeeds and MH-Weed16 benchmark datasets)
  - Model availability, architecture metadata, and checkpoint status
  - Strict confidence gating and honest degradation reporting
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class WeedBoundingBox(BaseModel):
    """Normalized bounding box coordinates [0.0 - 1.0] if localization is supported."""
    ymin: float = Field(..., ge=0.0, le=1.0, description="Normalized top coordinate")
    xmin: float = Field(..., ge=0.0, le=1.0, description="Normalized left coordinate")
    ymax: float = Field(..., ge=0.0, le=1.0, description="Normalized bottom coordinate")
    xmax: float = Field(..., ge=0.0, le=1.0, description="Normalized right coordinate")
    label: Optional[str] = Field(None, description="Class label for this detection")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Localization confidence")


class DetectedWeedItem(BaseModel):
    """Structured detection record for a single weed species or bounding box instance."""
    weed_name: str = Field(..., description="Common vernacular weed name (e.g., Parthenium / Congress Grass)")
    scientific_name: Optional[str] = Field(None, description="Botanical binomial taxon")
    weed_class_id: int = Field(..., description="Dataset integer class ID")
    source_dataset: str = Field(..., description="Benchmark dataset origin: 'DeepWeeds' or 'MH-Weed16'")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model prediction confidence [0.0 - 1.0]")
    bounding_box: Optional[WeedBoundingBox] = Field(
        None,
        description="Bounding box coordinates if model architecture performs object detection"
    )
    detection_type: Literal["OBJECT_DETECTION", "IMAGE_CLASSIFICATION"] = Field(
        "IMAGE_CLASSIFICATION",
        description="Detection granularity: whether bounding boxes exist or image-level classification"
    )
    growth_habit: Optional[str] = Field(
        None,
        description="Botanical classification: 'broadleaf', 'grass', 'sedge', 'woody_shrub', 'vine'"
    )
    description: Optional[str] = Field(None, description="Agro-ecological weed profile and invasiveness")


class WeedModelInfo(BaseModel):
    """Metadata regarding the registered weed detection model and runtime engine."""
    model_id: str = Field(..., description="Identifier of the model/pipeline")
    model_name: str = Field(..., description="Human-readable model name")
    architecture: str = Field(..., description="Neural network architecture family (e.g. ResNet50, YOLO)")
    task_type: Literal["IMAGE_CLASSIFICATION", "OBJECT_DETECTION"] = Field(
        ...,
        description="Core task supported by the underlying neural architecture"
    )
    supports_bounding_boxes: bool = Field(
        ...,
        description="True only if model genuinely outputs spatial bounding boxes"
    )
    is_operational: bool = Field(..., description="True if weights are loaded and ready for inference")
    checkpoint_path: Optional[str] = Field(None, description="Filesystem path where weights are loaded or expected")
    supported_classes_count: int = Field(..., description="Number of recognized weed classes in catalog")
    dataset_origin: str = Field(..., description="Benchmark dataset origin ('DeepWeeds' or 'MH-Weed16')")
    framework: str = Field("PyTorch / Ultralytics / ONNX", description="Underlying inference runtime framework")
    license: str = Field("Apache-2.0 / CC BY 4.0", description="Model weights and dataset license")
    status_message: str = Field(..., description="Operational status or explanation if unavailable")
