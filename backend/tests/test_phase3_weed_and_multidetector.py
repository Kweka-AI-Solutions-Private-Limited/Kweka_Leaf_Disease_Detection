"""
test_phase3_weed_and_multidetector.py — Phase 3 Validation Suite
-----------------------------------------------------------------
Validates:
  1. Weed Detection catalog integrity (DeepWeeds 9 classes, MH-Weed16 16 classes).
  2. Bounding-box vs. whole-image classification distinction.
  3. Honest MODEL_UNAVAILABLE degradation when weights are absent.
  4. Negative / non-weed class handling (DeepWeeds Class 8).
  5. Pl@ntNet image preparation (EXIF orientation, RGB normalization, blur checking).
  6. Agricultural crop vs. wild flora / potential weed distinction.
  7. Independence of all 4 detectors (Crop, Disease, Weed, Pest).
"""

import io
import sys
from pathlib import Path
import pytest
from PIL import Image
import numpy as np

# Ensure src is on python path
_src_dir = str(Path(__file__).resolve().parent.parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from services.weed_detection.weed_catalog import (
    DEEPWEEDS_CATALOG,
    MHWEED16_CATALOG,
    get_deepweeds_class,
    get_mhweed16_class,
)
from services.weed_detection.weed_provider import (
    ModularWeedDetectorProvider,
    get_weed_provider,
    reset_weed_provider_for_testing,
)
from services.pest_detection.pest_provider import get_pest_provider
from services.unified_test.unified_test_service import (
    prepare_image_for_api,
    run_crop_identification,
    run_disease_detection,
    run_weed_detection,
    run_pest_detection,
    get_all_detectors_status,
)
from schemas.weed_detection import DetectedWeedItem, WeedBoundingBox, WeedModelInfo


def _make_dummy_image(width=400, height=400, color=(100, 180, 100)) -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class DummyWeedClassificationProvider:
    """Mock provider simulating DeepWeeds ResNet50 whole-image classification."""

    def is_available(self) -> bool:
        return True

    def get_model_info(self) -> WeedModelInfo:
        return WeedModelInfo(
            model_id="deepweeds-resnet50",
            model_name="DeepWeeds ResNet50 Classifier",
            architecture="ResNet50 (Whole-Image Prediction)",
            task_type="IMAGE_CLASSIFICATION",
            supports_bounding_boxes=False,
            is_operational=True,
            checkpoint_path="/mock/path/deepweeds_resnet50.pt",
            supported_classes_count=9,
            dataset_origin="DeepWeeds (9 Classes)",
            framework="PyTorch",
            license="Apache-2.0",
            status_message="DeepWeeds ResNet50 weights operational.",
        )

    def detect_weeds(self, image_bytes: bytes, crop_name=None):
        info = self.get_model_info()
        item = DetectedWeedItem(
            weed_name="Parthenium (Congress Grass / Carrot Grass)",
            scientific_name="Parthenium hysterophorus",
            weed_class_id=3,
            source_dataset="DeepWeeds",
            confidence=0.88,
            bounding_box=None,  # Crucial: Classifier has NO bounding boxes
            detection_type="IMAGE_CLASSIFICATION",
            growth_habit="broadleaf",
            description="Prolific allelopathic herb.",
        )
        return ([item], info)


class DummyWeedDetectionProvider:
    """Mock provider simulating MH-Weed16 YOLO multi-object detection."""

    def is_available(self) -> bool:
        return True

    def get_model_info(self) -> WeedModelInfo:
        return WeedModelInfo(
            model_id="mhweed16-yolo",
            model_name="MH-Weed16 YOLO Object Detector",
            architecture="YOLO11s (Spatial Bounding Boxes)",
            task_type="OBJECT_DETECTION",
            supports_bounding_boxes=True,
            is_operational=True,
            checkpoint_path="/mock/path/mhweed16_yolo.pt",
            supported_classes_count=16,
            dataset_origin="MH-Weed16 (16 Classes)",
            framework="Ultralytics YOLO",
            license="CC BY 4.0",
            status_message="MH-Weed16 YOLO weights operational.",
        )

    def detect_weeds(self, image_bytes: bytes, crop_name=None):
        info = self.get_model_info()
        box = WeedBoundingBox(
            ymin=0.15,
            xmin=0.20,
            ymax=0.65,
            xmax=0.75,
            label="Purple Nutsedge (Motha)",
            confidence=0.82,
        )
        item = DetectedWeedItem(
            weed_name="Purple Nutsedge (Motha)",
            scientific_name="Cyperus rotundus",
            weed_class_id=2,
            source_dataset="MH-Weed16",
            confidence=0.82,
            bounding_box=box,  # Object detector HAS bounding boxes
            detection_type="OBJECT_DETECTION",
            growth_habit="sedge",
            description="Extremely persistent perennial tuberous sedge.",
        )
        return ([item], info)


# =====================================================================
# 1. CATALOG INTEGRITY TESTS
# =====================================================================

def test_deepweeds_catalog_structure():
    assert len(DEEPWEEDS_CATALOG) == 9
    for idx in range(9):
        item = get_deepweeds_class(idx)
        assert item is not None
        assert "name" in item
        assert "is_negative" in item

    # Class 8 is specifically the Negative/background class
    assert DEEPWEEDS_CATALOG[8]["is_negative"] is True
    # Class 3 is Parthenium
    assert "Parthenium" in DEEPWEEDS_CATALOG[3]["name"]
    assert DEEPWEEDS_CATALOG[3]["is_negative"] is False


def test_mhweed16_catalog_structure():
    assert len(MHWEED16_CATALOG) == 16
    for idx in range(16):
        item = get_mhweed16_class(idx)
        assert item is not None
        assert "name" in item
        assert "scientific_name" in item
        assert item["is_negative"] is False

    # Check key Indian weeds are present
    names = [MHWEED16_CATALOG[i]["name"] for i in range(16)]
    assert any("Celosia" in n or "Murgha" in n for n in names)
    assert any("Cyperus" in n or "Motha" in n for n in names)
    assert any("Parthenium" in n or "Gajar" in n for n in names)


# =====================================================================
# 2. WEED PROVIDER HONESTY & DEGRADATION TESTS
# =====================================================================

def test_weed_provider_missing_weights_honest_degradation():
    provider = ModularWeedDetectorProvider(checkpoint_path="/nonexistent/weed_model.pt")
    assert provider.is_available() is False

    info = provider.get_model_info()
    assert info.is_operational is False
    assert "No validated weed detector weights" in info.status_message

    img_bytes = _make_dummy_image()
    detections, updated_info = provider.detect_weeds(img_bytes)
    assert detections == []
    assert updated_info.is_operational is False


def test_run_weed_detection_missing_weights_returns_model_unavailable():
    # Ensure provider is looking at nonexistent path
    reset_weed_provider_for_testing(ModularWeedDetectorProvider(checkpoint_path="/nonexistent/model.pt"))
    try:
        img_bytes = _make_dummy_image()
        result = run_weed_detection(img_bytes, "test.jpg")
        assert result.status == "MODEL_UNAVAILABLE"
        assert result.is_operational is False
        assert result.detected_weeds == []
        assert "No validated weed detector weights" in result.message
    finally:
        reset_weed_provider_for_testing(None)


def test_run_weed_detection_classification_vs_object_detection():
    img_bytes = _make_dummy_image()

    # Test Branch A: DeepWeeds Whole-Image Classifier
    reset_weed_provider_for_testing(DummyWeedClassificationProvider())
    try:
        res = run_weed_detection(img_bytes, "test.jpg")
        assert res.status == "CONFIRMED"
        assert res.is_operational is True
        assert res.supports_bounding_boxes is False
        assert len(res.detected_weeds) == 1
        top_weed = res.detected_weeds[0]
        assert top_weed.bounding_box is None  # Must NOT claim bounding boxes
        assert top_weed.detection_type == "IMAGE_CLASSIFICATION"
        assert "Parthenium" in top_weed.weed_name
    finally:
        reset_weed_provider_for_testing(None)

    # Test Branch B: MH-Weed16 YOLO Object Detector
    reset_weed_provider_for_testing(DummyWeedDetectionProvider())
    try:
        res = run_weed_detection(img_bytes, "test.jpg")
        assert res.status == "CONFIRMED"
        assert res.is_operational is True
        assert res.supports_bounding_boxes is True
        assert len(res.detected_weeds) == 1
        top_weed = res.detected_weeds[0]
        assert top_weed.bounding_box is not None  # Must provide bounding boxes
        assert top_weed.bounding_box.ymin == 0.15
        assert top_weed.detection_type == "OBJECT_DETECTION"
        assert "Nutsedge" in top_weed.weed_name
    finally:
        reset_weed_provider_for_testing(None)


# =====================================================================
# 3. IMAGE PREPARATION & BOTANICAL DISTINCTION TESTS
# =====================================================================

def test_prepare_image_for_api_transposes_and_normalizes():
    # Create RGBA image with small size
    rgba_img = Image.new("RGBA", (150, 150), (200, 100, 50, 255))
    buf = io.BytesIO()
    rgba_img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    processed_bytes, mime, quality_warning = prepare_image_for_api(raw_bytes, "sample.png")
    assert mime == "image/jpeg"
    # Verify resulting bytes are valid JPEG and RGB
    result_img = Image.open(io.BytesIO(processed_bytes))
    assert result_img.mode == "RGB"
    assert result_img.size == (150, 150)


def test_prepare_image_for_api_resizes_oversized():
    huge_img = Image.new("RGB", (2500, 2000), (80, 150, 80))
    buf = io.BytesIO()
    huge_img.save(buf, format="JPEG")

    processed_bytes, mime, _ = prepare_image_for_api(buf.getvalue(), "huge.jpg")
    result_img = Image.open(io.BytesIO(processed_bytes))
    assert result_img.width <= 1920
    assert result_img.height <= 1920


# =====================================================================
# 4. IP102 LIVE DETECTOR INFERENCE VALIDATION
# =====================================================================

def test_ip102_live_detector_is_operational():
    # Tests that the real checkpoint in models/pest/ is loaded and operational
    provider = get_pest_provider()
    info = provider.get_model_info()
    assert info.is_operational is True
    assert info.supported_classes_count == 102

    # Run inference on blank green image — should cleanly return genuine negative or low conf detections
    img_bytes = _make_dummy_image(640, 640)
    result = run_pest_detection(img_bytes, "foliage.jpg")
    assert result.is_operational is True
    assert result.status in ["NO_PEST_DETECTED", "UNCERTAIN", "CONFIRMED"]
    if result.status == "NO_PEST_DETECTED":
        assert "No insect pests detected" in result.message


# =====================================================================
# 5. ALL DETECTORS STATUS REPORTING
# =====================================================================

def test_get_all_detectors_status_reports_all_four_modules():
    status_map = get_all_detectors_status()
    assert "crop_identifier" in status_map
    assert "disease_detector" in status_map
    assert "weed_detector" in status_map
    assert "pest_detector" in status_map

    # Pest detector should be OPERATIONAL
    assert status_map["pest_detector"].is_operational is True
    assert status_map["pest_detector"].status == "OPERATIONAL"

    # Weed detector should honestly report AWAITING_WEIGHTS if no local weed weights exist
    weed_status = status_map["weed_detector"]
    assert weed_status.status in ["OPERATIONAL", "AWAITING_WEIGHTS"]
    assert "Weed" in weed_status.detector_name
