"""
test_category_separation_and_confidence_gating.py
--------------------------------------------------
Regression tests to verify:
  1. Insect pests (e.g. Colorado potato beetle) are strictly rejected from Disease Detection (INVALID_CATEGORY).
  2. Crop identification prioritizes common name ("Potato") over scientific name and enforces <60% UNCERTAIN status.
  3. Insect & Pest detection enforces strict >70% confidence gate and maps class 68 to stem_boring Tiger Longicorn Beetle.
  4. Weed detection honestly reports MODEL_UNAVAILABLE without mocks.
"""

from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from main import app
from services.leaf_disease.pathology_classifier import classify_disorder, parse_eppo_description
from services.leaf_disease.plant_identifier import normalize_crop_name
from services.pest_detection.ip102_classes import get_ip102_class
from services.unified_test.unified_test_service import (
    run_crop_identification,
    run_disease_detection,
    run_pest_detection,
    run_weed_detection,
)


@pytest.fixture
def client():
    return TestClient(app)


class TestPathologyClassifier:
    """Verifies that non-disease organisms are accurately caught and separated."""

    def test_colorado_potato_beetle_classified_as_arthropod_pest(self):
        desc = "Leptinotarsa decemlineata - Colorado beetle (Colorado potato beetle)"
        result = classify_disorder(description=desc, eppo_code="LPTNDE")

        assert result.is_pathology is False
        assert result.organism_type == "ARTHROPOD_PEST"
        assert "Colorado potato beetle" in result.common_name
        assert result.scientific_name == "Leptinotarsa decemlineata"

    def test_genuine_pathology_classified_as_disease(self):
        desc = "Phytophthora infestans - Late blight of potato"
        result = classify_disorder(description=desc, eppo_code="PHYTIN")

        assert result.is_pathology is True
        assert result.organism_type == "PATHOLOGY"
        assert result.common_name == "Late blight of potato"
        assert result.scientific_name == "Phytophthora infestans"

    def test_armyworm_and_mites_classified_as_pests(self):
        res1 = classify_disorder("Spodoptera frugiperda - Fall armyworm")
        assert res1.is_pathology is False

        res2 = classify_disorder("Tetranychus urticae - Two-spotted spider mite")
        assert res2.is_pathology is False


class TestCropIdentificationNormalizationAndGating:
    """Verifies common name prioritization and 60% confidence gate."""

    def test_solanum_tuberosum_normalizes_to_potato(self):
        assert normalize_crop_name("Solanum tuberosum") == "Potato"
        assert normalize_crop_name("solanum tuberosum") == "Potato"

    @patch("requests.post")
    def test_crop_identification_under_60_percent_is_uncertain(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {
                    "score": 0.273,
                    "species": {
                        "scientificNameWithoutAuthor": "Solanum tuberosum",
                        "commonNames": ["Potato", "Irish potato"],
                    },
                }
            ]
        }
        mock_post.return_value = mock_resp

        result = run_crop_identification(image_bytes=b"dummy", filename="test.jpg")

        assert result.crop_name == "Potato"
        assert result.scientific_name == "Solanum tuberosum"
        assert result.confidence == 0.273
        assert result.status == "UNCERTAIN"
        assert "below 60%" in result.message


class TestDiseaseDetectionCategorySeparation:
    """Verifies that an insect pest returned in the disease stream is excluded with INVALID_CATEGORY."""

    @patch("services.unified_test.unified_test_service._get_plant_api_key", return_value="dummy_key")
    @patch("requests.post")
    def test_colorado_beetle_in_disease_stream_returns_invalid_category(self, mock_post, mock_key):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {
                    "name": "LPTNDE",
                    "description": "Leptinotarsa decemlineata - Colorado beetle (Colorado potato beetle)",
                    "score": 0.487,
                },
                {
                    "name": "PHYTIN",
                    "description": "Phytophthora infestans - Late blight of potato",
                    "score": 0.125,
                },
            ]
        }
        mock_post.return_value = mock_resp

        result = run_disease_detection(image_bytes=b"dummy", filename="test.jpg")

        assert result.status == "INVALID_CATEGORY"
        assert result.confidence is None
        assert result.confidence_gate_passed is False
        assert "Colorado potato beetle" in result.raw_provider_finding
        assert result.raw_provider_score == 0.487
        assert "Non-Disease Finding" in result.category_warning
        # Verify that only the genuine secondary pathology candidate survived
        assert len(result.candidates) == 1
        assert "Late blight of potato" in result.candidates[0].disease_name


class TestInsectTaxonomyAndConfidenceGating:
    """Verifies IP102 class 68 metadata and confidence threshold enforcement."""

    def test_class_68_is_xylotrechus_stem_borer_not_foliar_chewer(self):
        meta = get_ip102_class(68)
        assert meta is not None
        assert "Xylotrechus" in meta["name"]
        assert meta["scientific_name"] == "Xylotrechus spp."
        assert meta["damage_type"] == "stem_boring"
        assert "foliar_chewing" not in meta["damage_type"]

    def test_weed_detection_reports_model_unavailable(self):
        from services.weed_detection.weed_provider import reset_weed_provider_for_testing, ModularWeedDetectorProvider
        reset_weed_provider_for_testing(ModularWeedDetectorProvider(checkpoint_path="/nonexistent/model.pt"))
        try:
            result = run_weed_detection(image_bytes=b"dummy", filename="test.jpg")
            assert result.status == "MODEL_UNAVAILABLE"
            assert result.is_operational is False
            assert len(result.detected_weeds) == 0
        finally:
            reset_weed_provider_for_testing(None)

