"""
test_phase2_pest_detection.py — Comprehensive Automated Test Suite for Phase 2
--------------------------------------------------------------------------------
Covers:
  1. Image validation (valid, corrupt, blurry, formats, size limits)
  2. Crop selection & host compatibility matrix
  3. IP102 catalog ontology (102 classes, specimen vs damage distinction)
  4. Strict >70% confidence threshold gating (above 70% vs at/below 70%)
  5. Multiple pest detections (multi-object bounding boxes)
  6. Model availability & honest degraded handling (zero hallucination guarantee)
  7. Pest FastAPI endpoint (/api/pest-detection/analyze, status, classes)
  8. Regression protection for Phase 1 Disease Detection endpoint (/api/leaf-disease/analyze)

NOTE: Per implementation policy, test cases are authored here for consolidated
execution during the integration validation stage.
"""

import io
import os
import sys
from pathlib import Path
import pytest
from PIL import Image
from fastapi.testclient import TestClient

# Ensure backend src is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
src_dir = backend_dir / "src"
for p in [str(backend_dir), str(src_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from schemas.leaf_disease import OverallImageValidationResult, ImageValidationDetail, CropIdentificationResult
from schemas.pest_detection import (
    DetectedPestItem,
    PestBoundingBox,
    PestModelInfo,
    PestValidationResult,
    PestDetectionAnalysisResponse,
)
from services.leaf_disease.image_validator import validate_single_image, validate_multiple_images
from services.leaf_disease.plant_identifier import identify_crop, normalize_crop_name
from services.pest_detection.ip102_classes import (
    IP102_CATALOG,
    get_ip102_class,
    find_ip102_class_by_name,
    get_supported_pest_classes,
    is_crop_susceptible,
    classify_pest_type_distinction,
)
from services.pest_detection.pest_provider import (
    PestDetectionProvider,
    IP102LocalDetectorProvider,
    HarnessTestPestProvider,
    set_pest_provider_for_testing,
)
from services.pest_detection.pest_validator import validate_pest_findings, STRICT_CONFIDENCE_THRESHOLD


def create_test_image(format="JPEG", size=(300, 300), color=(100, 180, 100)) -> bytes:
    """Creates in-memory image bytes for test fixtures."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def make_valid_detail(blur_score=60.0, brightness=130.0) -> ImageValidationDetail:
    """Helper to generate a validated ImageValidationDetail fixture."""
    return ImageValidationDetail(
        filename="test_pest.jpg",
        is_valid=True,
        format="JPEG",
        width=400,
        height=400,
        size_bytes=4000,
        blur_score=blur_score,
        brightness=brightness,
        errors=[],
        warnings=[],
    )


# ==============================================================================
# 1. IMAGE VALIDATION TESTS (SHARED UTILITY IN PEST CONTEXT)
# ==============================================================================

class TestPestImageValidation:
    def test_valid_pest_image_formats(self):
        for fmt in ["JPEG", "PNG", "WEBP"]:
            img_bytes = create_test_image(format=fmt)
            detail = validate_single_image(f"leaf.{fmt.lower()}", img_bytes)
            assert detail.is_valid is True
            assert detail.errors == []

    def test_corrupt_pest_image_rejected(self):
        corrupt_bytes = b"NOT_A_VALID_IMAGE_HEADER_DATA"
        detail = validate_single_image("corrupt.jpg", corrupt_bytes)
        assert detail.is_valid is False
        assert any("corrupt" in e.lower() or "unidentified" in e.lower() or "header" in e.lower() for e in detail.errors)

    def test_low_resolution_image_rejected(self):
        tiny_bytes = create_test_image(size=(80, 80))
        detail = validate_single_image("tiny.jpg", tiny_bytes)
        assert detail.is_valid is False
        assert any("resolution" in e.lower() for e in detail.errors)

    def test_blurry_image_triggers_quality_warning(self):
        # A single solid color image produces zero Laplacian variance (blurry)
        flat_bytes = create_test_image(color=(128, 128, 128))
        detail = validate_single_image("flat.jpg", flat_bytes)
        assert detail.is_valid is True
        assert any("blur" in w.lower() for w in detail.warnings)


# ==============================================================================
# 2. CROP SELECTION & HOST COMPATIBILITY TESTS
# ==============================================================================

class TestCropSelectionAndHostCompatibility:
    def test_user_crop_selection_propagated(self):
        crop_res = identify_crop(selected_crop="Tomato")
        assert crop_res.crop_name == "Tomato"
        assert crop_res.status == "USER_SPECIFIED"

    def test_compatible_crop_and_pest_pairing(self):
        # Rice Leaf Roller (class 0) on Rice is a known compatible pairing
        is_compat = is_crop_susceptible("Rice / Paddy", class_id=0)
        assert is_compat is True

    def test_host_mismatch_triggers_penalty(self):
        # European Corn Borer (class 9) on Citrus is a mismatch
        is_compat = is_crop_susceptible("Lemon / Citrus", class_id=9)
        assert is_compat is False

    def test_unspecified_crop_is_unrestricted(self):
        # Unspecified crop allows all pests without automatic mismatch rejection
        assert is_crop_susceptible("Unspecified", class_id=0) is True
        assert is_crop_susceptible("Unknown", class_id=10) is True


# ==============================================================================
# 3. IP102 CATALOG ONTOLOGY & SPECIMEN/DAMAGE DISTINCTION
# ==============================================================================

class TestIP102CatalogOntology:
    def test_ip102_catalog_contains_102_classes(self):
        classes = get_supported_pest_classes()
        assert len(classes) == 102
        # Check specific benchmark species exist
        ids = [c["id"] for c in classes]
        assert 0 in ids  # Rice Leaf Roller
        assert 10 in ids  # Fall Armyworm
        assert 16 in ids  # Whitefly
        assert 20 in ids  # Thrips

    def test_class_lookup_by_id_and_name(self):
        c0 = get_ip102_class(0)
        assert c0 is not None
        assert "Rice Leaf Roller" in c0["name"]

        found = find_ip102_class_by_name("Fall Armyworm")
        assert found is not None
        assert found["id"] == 10

    def test_specimen_vs_damage_distinction(self):
        assert classify_pest_type_distinction("INSECT") == "SPECIMEN_DETECTED"
        assert classify_pest_type_distinction("LARVA") == "SPECIMEN_DETECTED"
        assert classify_pest_type_distinction("PEST_DAMAGE") == "DAMAGE_ONLY"
        assert classify_pest_type_distinction("OTHER") == "UNCERTAIN"


# ==============================================================================
# 4. STRICT >70% CONFIDENCE GATE TESTS
# ==============================================================================

class TestStrictConfidenceGate:
    def test_confidence_above_70_qualifies_for_confirmation(self):
        pest = DetectedPestItem(
            pest_name="Fall Armyworm",
            scientific_name="Spodoptera frugiperda",
            pest_class_id=10,
            category="LARVA",
            confidence=0.88,
            damage_type="foliar_chewing",
        )
        crop_info = CropIdentificationResult(
            crop_name="Corn (Maize)",
            source="user_selected",
            status="USER_SPECIFIED",
            evidence_note="User selected",
        )
        val_img = OverallImageValidationResult(
            total_submitted=1, valid_count=1, invalid_count=0, is_any_valid=True, details=[make_valid_detail()]
        )
        model_info = PestModelInfo(
            model_id="test-model",
            model_name="Test Model",
            architecture="YOLOv8",
            is_operational=True,
            checkpoint_path="test.onnx",
            supported_classes_count=102,
            framework="ONNX",
            license="Apache-2.0",
            status_message="OK",
        )

        res = validate_pest_findings([pest], crop_info, val_img, model_info)
        # Strict rule: confidence > 0.70 with good quality and compatible host MUST confirm
        assert res.confidence_gate_passed is True
        assert res.calibrated_confidence > 0.70
        assert res.is_uncertain is False
        assert res.diagnosis_status == "CONFIRMED"
        assert res.evidence_level == "HIGH"

    def test_confidence_at_or_below_70_strictly_uncertain(self):
        # Even at 0.70 exactly, must remain UNCERTAIN (strict > 0.70 rule)
        pest = DetectedPestItem(
            pest_name="Fall Armyworm",
            pest_class_id=10,
            category="LARVA",
            confidence=0.70,
            damage_type="foliar_chewing",
        )
        crop_info = CropIdentificationResult(
            crop_name="Corn (Maize)",
            source="user_selected",
            status="USER_SPECIFIED",
            evidence_note="User selected",
        )
        val_img = OverallImageValidationResult(
            total_submitted=1, valid_count=1, invalid_count=0, is_any_valid=True, details=[make_valid_detail()]
        )
        model_info = PestModelInfo(
            model_id="test-model",
            model_name="Test Model",
            architecture="YOLOv8",
            is_operational=True,
            checkpoint_path="test.onnx",
            supported_classes_count=102,
            framework="ONNX",
            license="Apache-2.0",
            status_message="OK",
        )

        res = validate_pest_findings([pest], crop_info, val_img, model_info)
        assert res.confidence_gate_passed is False
        assert res.is_uncertain is True
        assert res.diagnosis_status == "UNCERTAIN"
        assert res.retry_guidance is not None

    def test_high_confidence_demoted_on_suboptimal_image(self):
        # Raw confidence 0.78, but image has low blur variance (<12.0)
        pest = DetectedPestItem(
            pest_name="Whitefly",
            pest_class_id=16,
            category="INSECT",
            confidence=0.78,
            damage_type="sap_sucking",
        )
        crop_info = CropIdentificationResult(
            crop_name="Cotton",
            source="user_selected",
            status="USER_SPECIFIED",
            evidence_note="User selected",
        )
        blurry_detail = make_valid_detail(blur_score=8.5)
        val_img = OverallImageValidationResult(
            total_submitted=1, valid_count=1, invalid_count=0, is_any_valid=True, details=[blurry_detail]
        )
        model_info = PestModelInfo(
            model_id="test-model",
            model_name="Test Model",
            architecture="YOLOv8",
            is_operational=True,
            checkpoint_path="test.onnx",
            supported_classes_count=102,
            framework="ONNX",
            license="Apache-2.0",
            status_message="OK",
        )

        res = validate_pest_findings([pest], crop_info, val_img, model_info)
        # Quality penalty reduces calibrated confidence below 0.70
        assert res.calibrated_confidence <= 0.70
        assert res.is_uncertain is True
        assert res.diagnosis_status == "UNCERTAIN"


# ==============================================================================
# 5. MULTIPLE DETECTIONS & BOUNDING BOX LOCALIZATION TESTS
# ==============================================================================

class TestMultiPestLocalization:
    def test_multiple_visible_pests_detected(self):
        bbox1 = PestBoundingBox(ymin=0.1, xmin=0.1, ymax=0.4, xmax=0.4, label="Whitefly", confidence=0.85)
        bbox2 = PestBoundingBox(ymin=0.5, xmin=0.5, ymax=0.8, xmax=0.8, label="Cotton Aphid", confidence=0.76)

        pest1 = DetectedPestItem(
            pest_name="Whitefly", pest_class_id=16, category="INSECT", confidence=0.85, bounding_box=bbox1
        )
        pest2 = DetectedPestItem(
            pest_name="Cotton Aphid / Melon Aphid", pest_class_id=17, category="INSECT", confidence=0.76, bounding_box=bbox2
        )

        crop_info = CropIdentificationResult(crop_name="Cotton", source="user", status="USER_SPECIFIED", evidence_note="")
        val_img = OverallImageValidationResult(
            total_submitted=1, valid_count=1, invalid_count=0, is_any_valid=True, details=[make_valid_detail()]
        )
        model_info = PestModelInfo(
            model_id="test", model_name="Test", architecture="YOLOv8", is_operational=True,
            checkpoint_path="test.onnx", supported_classes_count=102, framework="ONNX", license="Apache-2.0", status_message="OK"
        )

        res = validate_pest_findings([pest1, pest2], crop_info, val_img, model_info)
        assert any("Multi-pest" in n for n in res.validation_notes)
        assert res.diagnosis_status == "CONFIRMED"

    def test_bounding_box_coordinates_normalized(self):
        bbox = PestBoundingBox(ymin=0.15, xmin=0.20, ymax=0.65, xmax=0.70, confidence=0.88)
        assert 0.0 <= bbox.ymin <= 1.0
        assert 0.0 <= bbox.xmin <= 1.0
        assert 0.0 <= bbox.ymax <= 1.0
        assert 0.0 <= bbox.xmax <= 1.0
        assert bbox.ymin < bbox.ymax
        assert bbox.xmin < bbox.xmax


# ==============================================================================
# 6. MODEL AVAILABILITY & HONEST DEGRADED HANDLING TESTS
# ==============================================================================

class TestModelAvailabilityAndHonesty:
    def test_unavailable_model_returns_model_unavailable_status(self):
        crop_info = CropIdentificationResult(crop_name="Tomato", source="user", status="USER_SPECIFIED", evidence_note="")
        val_img = OverallImageValidationResult(
            total_submitted=1, valid_count=1, invalid_count=0, is_any_valid=True, details=[make_valid_detail()]
        )
        offline_model_info = PestModelInfo(
            model_id="ip102-detector",
            model_name="IP102 Detector",
            architecture="YOLOv8",
            is_operational=False,
            checkpoint_path="models/pest/ip102_detector.onnx",
            supported_classes_count=102,
            framework="ONNX",
            license="Apache-2.0",
            status_message="Checkpoint not found at models/pest/ip102_detector.onnx",
        )

        res = validate_pest_findings([], crop_info, val_img, offline_model_info)
        assert res.diagnosis_status == "MODEL_UNAVAILABLE"
        assert res.calibrated_confidence == 0.0
        assert res.is_uncertain is True
        assert res.confidence_gate_passed is False

    def test_never_fabricate_pests_on_empty_detection(self):
        # Model is operational, but detects zero pests
        crop_info = CropIdentificationResult(crop_name="Rice", source="user", status="USER_SPECIFIED", evidence_note="")
        val_img = OverallImageValidationResult(
            total_submitted=1, valid_count=1, invalid_count=0, is_any_valid=True, details=[make_valid_detail()]
        )
        online_model_info = PestModelInfo(
            model_id="ip102-detector",
            model_name="IP102 Detector",
            architecture="YOLOv8",
            is_operational=True,
            checkpoint_path="test.onnx",
            supported_classes_count=102,
            framework="ONNX",
            license="Apache-2.0",
            status_message="Online",
        )

        res = validate_pest_findings([], crop_info, val_img, online_model_info)
        assert res.diagnosis_status == "NO_PEST_DETECTED"
        assert res.is_uncertain is True


# ==============================================================================
# 7. FASTAPI ENDPOINT INTEGRATION TESTS
# ==============================================================================

class TestFastApiPestEndpoints:
    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)

    def test_status_endpoint_reports_model_info(self, client):
        resp = client.get("/api/pest-detection/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "model_info" in data
        assert data["model_info"]["supported_classes_count"] == 102

    def test_classes_endpoint_lists_ip102(self, client):
        resp = client.get("/api/pest-detection/classes")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 102
        assert len(data["classes"]) == 102

    def test_zero_files_returns_400(self, client):
        resp = client.post("/api/pest-detection/analyze", headers={"X-User-ID": "usr_test"})
        assert resp.status_code in (400, 422)

    def test_more_than_five_files_returns_400(self, client):
        img_bytes = create_test_image()
        files = [("files", (f"pest_{i}.jpg", img_bytes, "image/jpeg")) for i in range(6)]
        resp = client.post(
            "/api/pest-detection/analyze",
            files=files,
            headers={"X-User-ID": "usr_test"}
        )
        assert resp.status_code == 400
        assert "Maximum 5 images allowed" in resp.json()["detail"]

    def test_pest_analysis_endpoint_lifecycle(self, client):
        # Configure harness provider with deterministic detection
        harness = HarnessTestPestProvider(initial_operational=True)
        harness.queue_detections([
            DetectedPestItem(
                pest_name="Fall Armyworm",
                scientific_name="Spodoptera frugiperda",
                pest_class_id=10,
                category="LARVA",
                confidence=0.89,
                damage_type="foliar_chewing",
                bounding_box=PestBoundingBox(ymin=0.2, xmin=0.2, ymax=0.7, xmax=0.7, confidence=0.89),
            )
        ])
        set_pest_provider_for_testing(harness)

        try:
            img_bytes = create_test_image()
            files = [("files", ("fall_armyworm.jpg", img_bytes, "image/jpeg"))]
            resp = client.post(
                "/api/pest-detection/analyze",
                files=files,
                data={"selected_crop": "Corn (Maize)"},
                headers={"X-User-ID": "usr_agronomist_01"}
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "SUCCESS"
            assert data["primary_pest"]["pest_name"] == "Fall Armyworm"
            assert data["validation_result"]["diagnosis_status"] == "CONFIRMED"
            assert data["validation_result"]["confidence_gate_passed"] is True
            assert "Phase 2" in data["phase_notice"]
        finally:
            set_pest_provider_for_testing(None)


# ==============================================================================
# 8. REGRESSION PROTECTION FOR PHASE 1 DISEASE ENDPOINT
# ==============================================================================

class TestPhase1RegressionProtection:
    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)

    def test_disease_endpoint_unaffected_regression(self, client):
        img_bytes = create_test_image()
        files = [("files", ("disease_leaf.jpg", img_bytes, "image/jpeg"))]
        resp = client.post(
            "/api/leaf-disease/analyze",
            files=files,
            headers={"X-User-ID": "usr_agronomist_01"}
        )
        # Should return valid disease analysis response without router interference
        assert resp.status_code == 200
        data = resp.json()
        assert "crop" in data
        assert "validation" in data
        assert "disease" in data
        assert "diagnosis" in data
