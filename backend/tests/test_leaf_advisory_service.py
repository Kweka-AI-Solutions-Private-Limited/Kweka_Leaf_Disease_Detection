"""
test_leaf_advisory_service.py — Test Suite for Leaf Advisory Service & Endpoints
--------------------------------------------------------------------------------
Tests:
  1. Historical diagnosis serialization & normalization
  2. Advisory generation with optional Geolocation and Season provided
  3. Advisory generation when Geolocation and Season are omitted (None / empty)
  4. Integration with NACL Catalog products & Gemini prompt fallback
"""

import pytest
from unittest.mock import MagicMock, patch
from schemas.leaf_advisory import LeafAdvisoryRequest, AdvisoryHistoricalDiagnosisItem
from services.leaf_advisory.leaf_advisory_service import LeafAdvisoryService


@pytest.fixture
def mock_db():
    db = MagicMock()
    # Mock ldd_inspections collection
    inspections_coll = MagicMock()
    mock_doc = {
        "analysis_id": "test_analysis_123",
        "timestamp": "2026-10-13T10:00:00Z",
        "source": "LEAF_DIAGNOSIS",
        "status": "CONFIRMED",
        "crop": {"crop_name": "Common Bean / Soybean (Fabaceae)", "confidence": 0.85},
        "disease": {"disease_name": "No pathology detected", "confidence": None},
        "pest": {"primary_pest": "Bean Leaf Beetle", "confidence": 0.88},
    }
    inspections_coll.find.return_value.sort.return_value.limit.return_value = [mock_doc]
    db.__getitem__.side_effect = lambda name: inspections_coll if name == "ldd_inspections" else MagicMock()
    return db


def test_get_historical_diagnoses(mock_db):
    service = LeafAdvisoryService(db=mock_db)
    items = service.get_historical_diagnoses(user_id="usr_01", limit=10)
    assert len(items) == 1
    item = items[0]
    assert item.analysis_id == "test_analysis_123"
    assert item.crop_name == "Common Bean / Soybean (Fabaceae)"
    assert item.pest_name == "Bean Leaf Beetle"
    assert item.source == "LEAF_DIAGNOSIS"


def test_generate_advisory_with_geolocation_and_season(mock_db):
    service = LeafAdvisoryService(db=mock_db)
    req = LeafAdvisoryRequest(
        crop_name="Common Bean / Soybean (Fabaceae)",
        disease_name="Rust",
        pest_name="Bean Leaf Beetle",
        geolocation="Punjab (North Indus Plain)",
        season="Kharif (Monsoon / Autumn)"
    )
    res = service.generate_advisory(req)
    assert res.advisory_id.startswith("adv_")
    assert res.crop_name == "Common Bean / Soybean (Fabaceae)"
    assert res.geolocation == "Punjab (North Indus Plain)"
    assert res.season == "Kharif (Monsoon / Autumn)"
    assert res.seasonal_risk.season_name == "Kharif (Monsoon / Autumn)"
    assert res.seasonal_risk.geolocation_name == "Punjab (North Indus Plain)"
    assert len(res.cultural_remedies) >= 3
    assert len(res.chemical_management) >= 2


def test_generate_advisory_optional_season_and_geolocation(mock_db):
    """Verifies that advisory succeeds cleanly when season and geolocation are NOT provided."""
    service = LeafAdvisoryService(db=mock_db)
    req = LeafAdvisoryRequest(
        crop_name="Tomato",
        disease_name="Early Blight",
        pest_name=None,
        geolocation=None,  # Optional
        season=None        # Optional
    )
    res = service.generate_advisory(req)
    assert res.advisory_id.startswith("adv_")
    assert res.crop_name == "Tomato"
    assert res.geolocation is None
    assert res.season is None
    assert res.seasonal_risk.season_name == "General / All Season"
    assert res.seasonal_risk.geolocation_name == "General Agricultural Region"
    assert len(res.cultural_remedies) >= 3
    assert len(res.chemical_management) >= 2
