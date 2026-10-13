"""
Comprehensive test suite for the Unified Testing Lab (Phase 1 & Phase 2).
Validates that all four detectors (Crop, Disease, Weed, Pest) operate independently,
accurately report their operational status, and adhere to the Zero-Hallucination
and Honest Degradation principles.
"""

import io
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from main import app
from services.pest_detection.pest_provider import get_pest_provider


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_leaf_image_bytes():
    img = Image.new("RGB", (320, 320), color=(60, 140, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestUnifiedTestingLab:
    def test_status_endpoint_reports_all_four_detectors(self, client):
        response = client.get("/api/unified-test/status")
        assert response.status_code == 200
        data = response.json()
        assert "detectors" in data
        detectors = data["detectors"]

        # Ensure all four independent detectors are present
        assert "crop_identifier" in detectors
        assert "disease_detector" in detectors
        assert "weed_detector" in detectors
        assert "pest_detector" in detectors

        # Verify pest detector status
        pest_status = detectors["pest_detector"]
        assert pest_status["detector_name"] == "Insect & Pest Detection"
        assert pest_status["status"] in ["OPERATIONAL", "AWAITING_WEIGHTS"]
        assert pest_status["type"] in ["Hybrid Engine (Spatial YOLO + EPPO Stream)", "Local Model (Offline)"]
        assert "IP102" in pest_status["provider"] or "YOLO" in pest_status["provider"]

    def test_analyze_endpoint_returns_independent_pest_results(self, client, sample_leaf_image_bytes):
        response = client.post(
            "/api/unified-test/analyze",
            files={"file": ("leaf.jpg", sample_leaf_image_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()

        # Check all top-level attributes
        assert "analysis_id" in data
        assert "timestamp" in data
        assert "image_validation" in data
        assert "crop" in data
        assert "disease" in data
        assert "weed" in data
        assert "pest" in data
        assert "notes" in data

        pest = data["pest"]
        assert pest is not None
        assert pest["status"] in ["NO_PEST_DETECTED", "CONFIRMED", "UNCERTAIN", "MODEL_UNAVAILABLE"]
        assert pest["supported_classes_count"] == 102
        assert isinstance(pest["detected_pests"], list)
        assert pest["is_operational"] is True

        # Plain green synthetic image should have genuine negative detection
        assert pest["status"] == "NO_PEST_DETECTED"
        assert len(pest["detected_pests"]) == 0
        assert "No insect pests detected" in pest["message"]

    def test_analyze_rejects_corrupted_image(self, client):
        corrupted_bytes = b"not_an_image_file_content"
        response = client.post(
            "/api/unified-test/analyze",
            files={"file": ("corrupt.jpg", corrupted_bytes, "image/jpeg")},
        )
        assert response.status_code == 400
        assert "Image validation failed" in response.json()["detail"]
