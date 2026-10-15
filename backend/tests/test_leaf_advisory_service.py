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


def test_generate_advisory_with_intake_and_acreage(mock_db):
    """Verifies that intake parameters, acreage calculations, pollinator alerts, and combinations work properly."""
    service = LeafAdvisoryService(db=mock_db)
    req = LeafAdvisoryRequest(
        crop_name="Cucumber",
        disease_name="Downy Mildew",
        growth_stage="Flowering",
        onset_days="1-2 days ago (Acute)",
        recent_weather="Rainy / High Humidity",
        previous_treatment="Already Sprayed - Ineffective",
        area_sown=2.5,
        area_unit="acres",
        severity_level="Severe (>30%)"
    )
    res = service.generate_advisory(req)
    assert res.advisory_id.startswith("adv_")
    assert res.escalation_required is True
    assert res.intake_summary is not None
    assert res.intake_summary["growth_stage"] == "Flowering"
    assert "2.5" in res.intake_summary["area_sown"]
    assert res.area_calculation_summary is not None
    assert "500 Liters" in res.area_calculation_summary
    assert res.combination_guidance is not None
    assert "Rainfastness" in res.combination_guidance or "Rotation" in res.combination_guidance

    # If products matched (e.g. Kadak for Cucumber Downy Mildew), check dosage & safety
    for p in res.nacl_products:
        assert p.calculated_total_water is not None
        assert "500 Liters" in p.calculated_total_water
        assert p.bee_toxicity_warning is not None
        assert "POLLINATOR" in p.bee_toxicity_warning


def test_zero_hallucination_on_unregistered_issue(mock_db):
    """Verifies that if no NACL product is registered for the crop/pathogen, NO random chemicals are recommended."""
    service = LeafAdvisoryService(db=mock_db)
    req = LeafAdvisoryRequest(
        crop_name="Dragonfruit",
        disease_name="Bacterial Soft Rot",
        growth_stage="Vegetative",
        recent_weather="Clear & Dry"
    )
    res = service.generate_advisory(req)
    # Zero hallucination guarantee: no off-label NACL products injected
    assert len(res.nacl_products) == 0
    # Must still provide safe remedies
    assert len(res.cultural_remedies) >= 3
    assert len(res.chemical_management) >= 1
    # Check that remedies address the issue safely
    combined_text = (res.ai_advisory_summary + " " + " ".join(res.cultural_remedies) + " " + " ".join(res.chemical_management)).lower()
    assert any(term in combined_text for term in ("bacterial", "sanitation", "drainage", "fertiliz", "irrigation", "prun", "nacl", "no registered"))
