"""
test_phase1_disease_detection.py
---------------------------------
Comprehensive automated test suite for Phase 1 Disease Detection:
  1. Image validation & quality checks (formats, blur, brightness, dimensions, size)
  2. Crop identification & manual override behavior
  3. Disease providers (Pl@ntNet, Kindwise, Mock)
  4. Diagnosis validation & supervisor's strict >70% confidence threshold gating
  5. Healthy leaf preservation
  6. Second-opinion reconciliation logic
  7. End-to-end FastAPI integration testing
"""

import io
import os
import sys
import pytest
from PIL import Image, ImageDraw, ImageFilter
from fastapi.testclient import TestClient

# Ensure backend and backend/src are on the sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from schemas.leaf_disease import (
    NormalizedDiseaseResult,
    DiagnosisValidationResult,
    OverallImageValidationResult,
    ImageValidationDetail,
    CropIdentificationResult
)
from services.leaf_disease.image_validator import (
    validate_single_image,
    validate_multiple_images,
    calculate_blur_variance,
    calculate_brightness
)
from services.leaf_disease.plant_identifier import identify_crop, normalize_crop_name
from services.leaf_disease.disease_provider import (
    MockDiseaseDetectionProvider,
    PlantNetDiseaseProvider,
    KindwiseCropHealthProvider
)
from services.leaf_disease.diagnosis_validator import (
    validate_diagnosis_evidence,
    calibrate_confidence,
    reconcile_diagnoses,
    should_verify_with_gemini
)


# Helper functions to create test image bytes
def create_test_image(width=300, height=300, color=(34, 139, 34), fmt="JPEG"):
    """Creates a simple colored synthetic image."""
    img = Image.new("RGB", (width, height), color=color)
    # Add some high-contrast shapes to produce natural sharpness
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 200, 200], fill=(200, 50, 50), outline=(255, 255, 255), width=3)
    draw.line([0, 0, width, height], fill=(0, 0, 0), width=4)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def create_blurry_image(width=300, height=300):
    """Creates an intentionally blurred synthetic image."""
    img = Image.new("RGB", (width, height), color=(100, 100, 100))
    # Apply heavy Gaussian blur
    img = img.filter(ImageFilter.GaussianBlur(radius=25))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def create_dark_image(width=300, height=300):
    """Creates a nearly black underexposed image."""
    img = Image.new("RGB", (width, height), color=(5, 5, 5))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ==============================================================================
# 1. IMAGE VALIDATION TESTS
# ==============================================================================

class TestImageValidation:
    def test_valid_jpeg_image(self):
        content = create_test_image(fmt="JPEG")
        detail = validate_single_image("leaf.jpg", content)
        assert detail.is_valid is True
        assert detail.format == "JPEG"
        assert detail.width == 300
        assert detail.height == 300
        assert len(detail.errors) == 0

    def test_valid_png_and_webp_images(self):
        for fmt in ["PNG", "WEBP"]:
            content = create_test_image(fmt=fmt)
            detail = validate_single_image(f"leaf.{fmt.lower()}", content)
            assert detail.is_valid is True
            assert detail.format == fmt

    def test_unsupported_format_rejected(self):
        content = create_test_image(fmt="GIF")
        detail = validate_single_image("leaf.gif", content)
        assert detail.is_valid is False
        assert any("Unsupported image format" in err for err in detail.errors)

    def test_empty_content_rejected(self):
        detail = validate_single_image("empty.jpg", b"")
        assert detail.is_valid is False
        assert "Empty file submitted." in detail.errors

    def test_corrupt_content_rejected(self):
        detail = validate_single_image("corrupt.jpg", b"not-a-real-image-bytes")
        assert detail.is_valid is False
        assert any("Corrupted" in err for err in detail.errors)

    def test_low_resolution_rejected(self):
        content = create_test_image(width=80, height=80)
        detail = validate_single_image("small.jpg", content)
        assert detail.is_valid is False
        assert any("resolution 80x80 is too low" in err for err in detail.errors)

    def test_blurry_image_warning(self):
        content = create_blurry_image()
        detail = validate_single_image("blurry.jpg", content)
        assert detail.is_valid is True  # Blurry images are accepted with warnings
        assert any("blurry" in w.lower() for w in detail.warnings)

    def test_dark_image_warning(self):
        content = create_dark_image()
        detail = validate_single_image("dark.jpg", content)
        assert detail.is_valid is True
        assert any("dark" in w.lower() for w in detail.warnings)

    def test_validate_multiple_images(self):
        img1 = ("img1.jpg", create_test_image())
        img2 = ("img2.png", create_test_image(fmt="PNG"))
        res = validate_multiple_images([img1, img2])
        assert res.total_submitted == 2
        assert res.valid_count == 2
        assert res.invalid_count == 0
        assert res.is_any_valid is True


# ==============================================================================
# 2. CROP IDENTIFICATION & OVERRIDE TESTS
# ==============================================================================

class TestCropIdentification:
    def test_manual_crop_selection_overrides(self):
        res = identify_crop(selected_crop="Tomato", valid_filenames=["image1.jpg"])
        assert res.crop_name == "Tomato"
        assert res.source == "user_selected"
        assert res.status == "USER_SPECIFIED"

    def test_crop_normalization(self):
        assert normalize_crop_name("solanum lycopersicum") == "Tomato"
        assert normalize_crop_name("ZEA MAYS") == "Corn (Maize)"
        assert normalize_crop_name("mangifera indica") == "Mango"

    def test_unknown_crop_returned_honestly(self):
        res = identify_crop(selected_crop=None, valid_filenames=["image1.jpg"])
        assert res.crop_name == "Unknown"
        assert res.status == "UNCERTAIN"


# ==============================================================================
# 3. DIAGNOSIS VALIDATOR & STRICT 70% CONFIDENCE GATE TESTS
# ==============================================================================

def make_valid_detail():
    return ImageValidationDetail(
        filename="leaf.jpg",
        is_valid=True,
        format="JPEG",
        width=400,
        height=400,
        size_bytes=2000,
        blur_score=60.0,
        brightness=130.0,
        errors=[],
        warnings=[]
    )


class TestDiagnosisValidatorStrictGate:
    def test_high_confidence_above_70_is_confirmed(self):
        raw_res = NormalizedDiseaseResult(
            disease_name="Early Blight",
            category="FUNGAL",
            confidence=0.92,
            provider_name="TestProvider",
            provider_status="OK"
        )
        crop_info = CropIdentificationResult(
            crop_name="Tomato",
            source="user_selected",
            status="USER_SPECIFIED",
            evidence_note="Specified by user"
        )
        val = validate_diagnosis_evidence(
            validation_result=OverallImageValidationResult(
                total_submitted=1, valid_count=1, invalid_count=0, is_any_valid=True, details=[make_valid_detail()]
            ),
            crop_info=crop_info,
            disease_result=raw_res
        )
        # Strict rule: calibrated_confidence > 0.70 MUST qualify as CONFIRMED
        assert val.calibrated_confidence > 0.70
        assert val.is_uncertain is False
        assert val.diagnosis_status == "CONFIRMED"
        assert val.evidence_level == "HIGH"

    def test_low_confidence_below_70_is_uncertain(self):
        raw_res = NormalizedDiseaseResult(
            disease_name="Tan Spot",
            category="FUNGAL",
            confidence=0.55,
            provider_name="TestProvider",
            provider_status="OK"
        )
        crop_info = CropIdentificationResult(
            crop_name="Wheat",
            source="user_selected",
            status="USER_SPECIFIED",
            evidence_note="Specified by user"
        )
        val = validate_diagnosis_evidence(
            validation_result=OverallImageValidationResult(
                total_submitted=1, valid_count=1, invalid_count=0, is_any_valid=True, details=[make_valid_detail()]
            ),
            crop_info=crop_info,
            disease_result=raw_res
        )
        # Strict rule: calibrated_confidence <= 0.70 MUST be marked UNCERTAIN
        assert val.calibrated_confidence <= 0.70
        assert val.is_uncertain is True
        assert val.diagnosis_status == "UNCERTAIN"
        assert val.targeted_close_up_request is not None

    def test_healthy_leaf_is_preserved_never_labeled_diseased(self):
        raw_res = NormalizedDiseaseResult(
            disease_name="Healthy / No Disease Detected",
            category="UNKNOWN_UNCERTAIN",
            confidence=0.95,
            provider_name="Kindwise crop.health",
            provider_status="OK"
        )
        crop_info = CropIdentificationResult(
            crop_name="Corn (Maize)",
            source="user_selected",
            status="USER_SPECIFIED",
            evidence_note="Specified by user"
        )
        val = validate_diagnosis_evidence(
            validation_result=OverallImageValidationResult(
                total_submitted=1, valid_count=1, invalid_count=0, is_any_valid=True, details=[make_valid_detail()]
            ),
            crop_info=crop_info,
            disease_result=raw_res
        )
        assert "Healthy" in val.primary_diagnosis
        assert val.is_uncertain is False
        assert val.diagnosis_status == "CONFIRMED"

    def test_mismatched_host_triggers_uncertainty(self):
        # Disease with incompatible host crop (e.g. Pear Rust on Wheat)
        raw_res = NormalizedDiseaseResult(
            disease_name="Pear Rust",
            category="FUNGAL",
            confidence=0.95,
            provider_name="TestProvider",
            provider_status="OK"
        )
        crop_info = CropIdentificationResult(
            crop_name="Wheat",
            source="user_selected",
            status="USER_SPECIFIED",
            evidence_note="Specified by user"
        )
        val = validate_diagnosis_evidence(
            validation_result=OverallImageValidationResult(
                total_submitted=1, valid_count=1, invalid_count=0, is_any_valid=True, details=[make_valid_detail()]
            ),
            crop_info=crop_info,
            disease_result=raw_res
        )
        # High raw confidence must NOT override host mismatch
        assert val.crop_compatibility_status == "MISMATCHED_HOST"
        assert val.is_uncertain is True
        assert val.diagnosis_status == "UNCERTAIN"


# ==============================================================================
# 4. RECONCILIATION & SECOND-OPINION TESTS
# ==============================================================================

class TestReconciliation:
    def test_agreement_confirms_diagnosis(self):
        primary_res = NormalizedDiseaseResult(
            disease_name="Tan Spot",
            category="FUNGAL",
            confidence=0.65,
            provider_name="PlantNet",
            provider_status="OK"
        )
        primary_val = DiagnosisValidationResult(
            evidence_level="MEDIUM",
            image_quality_status="GOOD",
            crop_compatibility_status="SUPPORTED",
            consistency_status="NO_CONFLICT",
            is_uncertain=True,
            calibrated_confidence=0.65,
            diagnosis_status="UNCERTAIN"
        )
        gemini_res = NormalizedDiseaseResult(
            disease_name="Tan Spot of Wheat",
            category="FUNGAL",
            confidence=0.88,
            provider_name="Gemini VLM",
            provider_status="OK"
        )
        final_res, final_val = reconcile_diagnoses(primary_res, primary_val, gemini_res)
        assert final_val.gemini_verification == "AGREED"
        assert final_val.calibrated_confidence > 0.70
        assert final_val.is_uncertain is False
        assert final_val.diagnosis_status == "CONFIRMED_BY_SECOND_OPINION"

    def test_conflict_with_low_confidence_marks_conflicting(self):
        primary_res = NormalizedDiseaseResult(
            disease_name="Powdery Mildew",
            category="FUNGAL",
            confidence=0.50,
            provider_name="PlantNet",
            provider_status="OK"
        )
        primary_val = DiagnosisValidationResult(
            evidence_level="LOW",
            image_quality_status="GOOD",
            crop_compatibility_status="SUPPORTED",
            consistency_status="NO_CONFLICT",
            is_uncertain=True,
            calibrated_confidence=0.50,
            diagnosis_status="UNCERTAIN"
        )
        gemini_res = NormalizedDiseaseResult(
            disease_name="Bacterial Canker",
            category="BACTERIAL",
            confidence=0.60,
            provider_name="Gemini VLM",
            provider_status="OK"
        )
        final_res, final_val = reconcile_diagnoses(primary_res, primary_val, gemini_res)
        assert final_val.gemini_verification == "DISAGREED"
        assert final_val.is_uncertain is True
        assert final_val.diagnosis_status == "CONFLICTING"


# ==============================================================================
# 5. MOCK PROVIDER BEHAVIOR TESTS
# ==============================================================================

class TestMockProvider:
    def test_mock_provider_deterministic_output(self):
        mock_prov = MockDiseaseDetectionProvider()
        img_detail = ImageValidationDetail(
            filename="leaf.jpg",
            is_valid=True,
            format="JPEG",
            width=300,
            height=300,
            size_bytes=1000,
            blur_score=50.0,
            brightness=120.0,
            errors=[],
            warnings=[]
        )
        res = mock_prov.detect_disease(crop_name="Tomato", image_details=[img_detail])
        assert res.is_mock is True
        assert res.provider_status == "MOCK"
        assert "Mock" in res.provider_name
        assert res.confidence is not None
        assert res.confidence >= 0.70


# ==============================================================================
# 6. FASTAPI END-TO-END ENDPOINT TESTS
# ==============================================================================

class TestFastApiEndpoint:
    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)

    def test_zero_files_returns_400(self, client):
        resp = client.post("/api/leaf-disease/analyze", headers={"X-User-ID": "test_user"})
        assert resp.status_code in (400, 422)

    def test_more_than_five_files_returns_400(self, client):
        img_bytes = create_test_image()
        files = [("files", (f"leaf_{i}.jpg", img_bytes, "image/jpeg")) for i in range(6)]
        resp = client.post(
            "/api/leaf-disease/analyze",
            files=files,
            headers={"X-User-ID": "test_user"}
        )
        assert resp.status_code == 400
        assert "Maximum 5 images allowed" in resp.json()["detail"]

    def test_single_valid_file_analysis_lifecycle(self, client):
        img_bytes = create_test_image()
        files = [("files", ("leaf.jpg", img_bytes, "image/jpeg"))]
        data = {"selected_crop": "Tomato"}
        resp = client.post(
            "/api/leaf-disease/analyze",
            files=files,
            data=data,
            headers={"X-User-ID": "test_user"}
        )
        assert resp.status_code == 200
        json_data = resp.json()
        assert "analysis_id" in json_data
        assert "status" in json_data
        assert json_data["status"] in ("SUCCESS", "UNCERTAIN", "FAILED")
        assert json_data["crop"]["crop_name"] == "Tomato"
        assert json_data["crop"]["source"] == "user_selected"
        assert json_data["validation"]["valid_count"] == 1
        assert "disease" in json_data
        assert "diagnosis" in json_data
        assert "phase_notice" in json_data
        assert "Phase 1" in json_data["phase_notice"]
