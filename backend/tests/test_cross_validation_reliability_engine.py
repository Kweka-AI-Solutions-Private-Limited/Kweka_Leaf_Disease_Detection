"""
test_cross_validation_reliability_engine.py — Complete Test Suite for Cross-Validation Engine
-----------------------------------------------------------------------------------------------
Covers all 20 required acceptance test cases deterministically:
 1. High-confidence crop and insect predictions with supported host relationship.
 2. Crop confidence below or equal to 70% (0.70 strictly fails).
 3. Insect confidence below or equal to 70% (0.70 strictly fails).
 4. Confidence above 70% with an unresolved host-pest conflict.
 5. Low crop confidence and high insect confidence.
 6. High crop confidence and low insect confidence.
 7. Unknown host-pest relationship.
 8. Incomplete host database (missing entry returns UNKNOWN, not INCOMPATIBLE).
 9. Unsupported or unknown insect class.
 10. Missing confidence values (represented honestly as uncalibrated/unavailable).
 11. Invalid, missing, or unavailable model weights.
 12. Poor-quality and invalid images.
 13. Disease and insect predictions that disagree.
 14. No disease detected without falsely declaring the plant healthy.
 15. No weed detected without declaring the field weed-free.
 16. Gemini routing requested while Gemini is disabled.
 17. Preservation of original model predictions.
 18. Prevention of crop-label changes based solely on host-pest compatibility.
 19. Prevention of one diagnostic category contaminating another.
 20. Regression tests for existing Phase 1 disease detection functionality.
"""

import pytest
from services.cross_validation.cross_validation_engine import (
    CrossValidationEngine,
    cross_validation_engine,
    STRICT_CONFIRMATION_THRESHOLD,
)
from services.cross_validation.host_pest_knowledge import (
    evaluate_host_pest_compatibility,
    HOST_PEST_PROFILES,
)
from schemas.cross_validation import (
    DiagnosticStatus,
    HostPestCompatibilityStatus,
    HostPestRelationshipType,
)
from services.leaf_disease.diagnosis_validator import (
    validate_diagnosis_evidence,
    calibrate_confidence,
)
from schemas.leaf_disease import (
    OverallImageValidationResult,
    ImageValidationDetail,
    CropIdentificationResult,
    NormalizedDiseaseResult,
)


@pytest.fixture
def engine():
    return CrossValidationEngine(enable_gemini_routing=False)


# =====================================================================
# 1. HIGH-CONFIDENCE CROP AND INSECT WITH SUPPORTED HOST RELATIONSHIP
# =====================================================================
def test_1_high_confidence_crop_and_insect_supported_host(engine):
    crop_data = {
        "crop_name": "Potato",
        "scientific_name": "Solanum tuberosum",
        "confidence": 0.88,
        "provider": "Pl@ntNet Species API v2",
        "status": "CONFIRMED",
    }
    pest_data = {
        "primary_pest": "Colorado Potato Beetle",
        "confidence": 0.82,
        "status": "CONFIRMED",
        "is_operational": True,
        "detected_pests": [{"pest_name": "Colorado Potato Beetle", "confidence": 0.82}],
    }
    disease_data = {"status": "NO_DISEASE_DETECTED", "disease_name": "No Disease Detected"}
    weed_data = {"status": "NO_WEED_DETECTED", "detected_weeds": []}

    res = engine.validate(crop_data, disease_data, pest_data, weed_data)

    assert res.crop_validation.diagnostic_status == DiagnosticStatus.CONFIRMED
    assert res.pest_validation.diagnostic_status == DiagnosticStatus.CONFIRMED
    assert res.host_pest_compatibility.compatibility_status == HostPestCompatibilityStatus.COMPATIBLE
    assert res.host_pest_compatibility.relationship_type == HostPestRelationshipType.ESTABLISHED_HOST
    assert res.verification_routing.verification_required is False
    assert len(res.detected_contradictions) == 0


# =====================================================================
# 2. CROP CONFIDENCE BELOW OR EQUAL TO 70% (0.70 MUST FAIL)
# =====================================================================
def test_2_crop_confidence_below_or_equal_70(engine):
    # Case A: Exactly 70% (0.70) must NOT pass confirmation
    crop_70 = {"crop_name": "Potato", "confidence": 0.70, "status": "CONFIRMED"}
    res_70 = engine.validate(
        crop_data=crop_70,
        disease_data={"status": "NO_DISEASE_DETECTED"},
        pest_data={"status": "NO_PEST_DETECTED"},
        weed_data={"status": "NO_WEED_DETECTED"},
    )
    assert res_70.crop_validation.confidence_gate_passed is False
    assert res_70.crop_validation.diagnostic_status == DiagnosticStatus.SUSPECTED
    assert res_70.crop_validation.diagnostic_status != DiagnosticStatus.CONFIRMED
    assert res_70.verification_routing.verification_required is True

    # Case B: Below 70% (0.65)
    crop_65 = {"crop_name": "Potato", "confidence": 0.65, "status": "UNCERTAIN"}
    res_65 = engine.validate(
        crop_data=crop_65,
        disease_data={"status": "NO_DISEASE_DETECTED"},
        pest_data={"status": "NO_PEST_DETECTED"},
        weed_data={"status": "NO_WEED_DETECTED"},
    )
    assert res_65.crop_validation.confidence_gate_passed is False
    assert res_65.crop_validation.diagnostic_status == DiagnosticStatus.SUSPECTED
    assert res_65.verification_routing.verification_required is True


# =====================================================================
# 3. INSECT CONFIDENCE BELOW OR EQUAL TO 70% (0.70 MUST FAIL)
# =====================================================================
def test_3_insect_confidence_below_or_equal_70(engine):
    # Case A: Exactly 70% (0.70) must NOT pass confirmation
    pest_70 = {
        "primary_pest": "Colorado Potato Beetle",
        "confidence": 0.70,
        "status": "CONFIRMED",
        "is_operational": True,
        "detected_pests": [{"pest_name": "Colorado Potato Beetle", "confidence": 0.70}],
    }
    res_70 = engine.validate(
        crop_data={"crop_name": "Potato", "confidence": 0.85},
        disease_data={"status": "NO_DISEASE_DETECTED"},
        pest_data=pest_70,
        weed_data={"status": "NO_WEED_DETECTED"},
    )
    assert res_70.pest_validation.confidence_gate_passed is False
    assert res_70.pest_validation.diagnostic_status == DiagnosticStatus.SUSPECTED
    assert res_70.pest_validation.diagnostic_status != DiagnosticStatus.CONFIRMED
    assert res_70.verification_routing.verification_required is True

    # Case B: Below 70% (0.55)
    pest_55 = {
        "primary_pest": "Colorado Potato Beetle",
        "confidence": 0.55,
        "status": "UNCERTAIN",
        "is_operational": True,
        "detected_pests": [{"pest_name": "Colorado Potato Beetle", "confidence": 0.55}],
    }
    res_55 = engine.validate(
        crop_data={"crop_name": "Potato", "confidence": 0.85},
        disease_data={"status": "NO_DISEASE_DETECTED"},
        pest_data=pest_55,
        weed_data={"status": "NO_WEED_DETECTED"},
    )
    assert res_55.pest_validation.confidence_gate_passed is False
    assert res_55.pest_validation.diagnostic_status == DiagnosticStatus.SUSPECTED
    assert res_55.verification_routing.verification_required is True


# =====================================================================
# 4. CONFIDENCE ABOVE 70% WITH UNRESOLVED HOST-PEST CONFLICT
# =====================================================================
def test_4_high_confidence_unresolved_host_pest_conflict(engine):
    # Potato (>70%) and Bean Leaf Beetle (>70%)
    crop_data = {"crop_name": "Potato", "confidence": 0.92, "status": "CONFIRMED"}
    pest_data = {
        "primary_pest": "Bean Leaf Beetle",
        "confidence": 0.85,
        "status": "CONFIRMED",
        "is_operational": True,
        "detected_pests": [{"pest_name": "Bean Leaf Beetle", "confidence": 0.85}],
    }
    res = engine.validate(
        crop_data=crop_data,
        disease_data={"status": "NO_DISEASE_DETECTED"},
        pest_data=pest_data,
        weed_data={"status": "NO_WEED_DETECTED"},
    )

    # Must detect biological inconsistency
    assert res.host_pest_compatibility.compatibility_status == HostPestCompatibilityStatus.INCOMPATIBLE
    assert res.host_pest_compatibility.relationship_type == HostPestRelationshipType.UNEXPECTED_HOST

    # Must demote pest to NEEDS_VERIFICATION instead of blindly confirming
    assert res.pest_validation.diagnostic_status == DiagnosticStatus.NEEDS_VERIFICATION

    # Must flag contradiction item
    assert any(c.code == "HIGH_CONFIDENCE_BIOLOGICAL_INCONSISTENCY" for c in res.detected_contradictions)

    # Must preserve original model predictions untouched
    assert res.crop_validation.predicted_label == "Potato"
    assert res.pest_validation.predicted_label == "Bean Leaf Beetle"
    assert res.crop_validation.original_model_score == 0.92
    assert res.pest_validation.original_model_score == 0.85


# =====================================================================
# 5. LOW CROP CONFIDENCE AND HIGH INSECT CONFIDENCE
# =====================================================================
def test_5_low_crop_confidence_high_insect_confidence(engine):
    # Illustrative case: Potato 26.6% and Colorado Potato Beetle 76.7%
    crop_data = {"crop_name": "Potato", "confidence": 0.266, "status": "UNCERTAIN"}
    pest_data = {
        "primary_pest": "Colorado Potato Beetle",
        "confidence": 0.767,
        "status": "CONFIRMED",
        "is_operational": True,
        "detected_pests": [{"pest_name": "Colorado Potato Beetle", "confidence": 0.767}],
    }
    res = engine.validate(
        crop_data=crop_data,
        disease_data={"status": "NO_DISEASE_DETECTED"},
        pest_data=pest_data,
        weed_data={"status": "NO_WEED_DETECTED"},
    )

    assert res.crop_validation.diagnostic_status == DiagnosticStatus.UNCERTAIN
    assert res.crop_validation.original_model_score == 0.266
    assert res.pest_validation.original_model_score == 0.767
    assert res.verification_routing.verification_required is True
    # Warning generated
    assert any("low confidence" in w.lower() for w in res.warnings)


# =====================================================================
# 6. HIGH CROP CONFIDENCE AND LOW INSECT CONFIDENCE
# =====================================================================
def test_6_high_crop_confidence_low_insect_confidence(engine):
    crop_data = {"crop_name": "Tomato", "confidence": 0.95, "status": "CONFIRMED"}
    pest_data = {
        "primary_pest": "Tobacco Whitefly",
        "confidence": 0.45,
        "status": "UNCERTAIN",
        "is_operational": True,
        "detected_pests": [{"pest_name": "Tobacco Whitefly", "confidence": 0.45}],
    }
    res = engine.validate(
        crop_data=crop_data,
        disease_data={"status": "NO_DISEASE_DETECTED"},
        pest_data=pest_data,
        weed_data={"status": "NO_WEED_DETECTED"},
    )

    assert res.crop_validation.diagnostic_status == DiagnosticStatus.CONFIRMED
    assert res.pest_validation.diagnostic_status == DiagnosticStatus.SUSPECTED
    assert "pest" in res.verification_routing.categories_needing_review


# =====================================================================
# 7. UNKNOWN HOST-PEST RELATIONSHIP
# =====================================================================
def test_7_unknown_host_pest_relationship(engine):
    # Exotic or uncataloged insect on a crop
    compat = evaluate_host_pest_compatibility("Potato", "Exotic Tree Cricket")
    assert compat.compatibility_status == HostPestCompatibilityStatus.UNKNOWN
    assert compat.relationship_type == HostPestRelationshipType.UNCERTAIN_RELATIONSHIP
    assert "catalog is incomplete" in compat.notes.lower()


# =====================================================================
# 8. INCOMPLETE HOST DATABASE DOES NOT PROVE INCOMPATIBILITY
# =====================================================================
def test_8_incomplete_host_database_returns_unknown(engine):
    compat = evaluate_host_pest_compatibility("Mustard / Rapeseed", "Uncataloged Agro Pest")
    assert compat.compatibility_status == HostPestCompatibilityStatus.UNKNOWN
    assert compat.compatibility_status != HostPestCompatibilityStatus.INCOMPATIBLE
    assert "do not treat unmapped entries as proof" in compat.notes.lower() or "not proof of incompatibility" in compat.notes.lower()


# =====================================================================
# 9. UNSUPPORTED OR UNKNOWN INSECT CLASS
# =====================================================================
def test_9_unsupported_or_unknown_insect_class(engine):
    pest_data = {
        "primary_pest": "Extraterrestrial Beetle #999",
        "confidence": 0.85,
        "status": "CONFIRMED",
        "is_operational": True,
        "detected_pests": [{"pest_name": "Extraterrestrial Beetle #999", "confidence": 0.85}],
    }
    res = engine.validate(
        crop_data={"crop_name": "Potato", "confidence": 0.85},
        disease_data={"status": "NO_DISEASE_DETECTED"},
        pest_data=pest_data,
        weed_data={"status": "NO_WEED_DETECTED"},
    )
    # Does not crash, handles unknown class gracefully
    assert res.host_pest_compatibility.compatibility_status == HostPestCompatibilityStatus.UNKNOWN


# =====================================================================
# 10. MISSING CONFIDENCE VALUES (HONEST REPRESENTATION)
# =====================================================================
def test_10_missing_confidence_values(engine):
    crop_data = {"crop_name": "Potato", "confidence": None, "status": "UNCERTAIN"}
    pest_data = {
        "primary_pest": "Colorado Potato Beetle",
        "confidence": None,
        "status": "UNCERTAIN",
        "is_operational": True,
        "detected_pests": [{"pest_name": "Colorado Potato Beetle", "confidence": None}],
    }
    res = engine.validate(
        crop_data=crop_data,
        disease_data={"status": "NO_DISEASE_DETECTED"},
        pest_data=pest_data,
        weed_data={"status": "NO_WEED_DETECTED"},
    )
    assert res.crop_validation.original_model_score is None
    assert res.crop_validation.diagnostic_status == DiagnosticStatus.UNCERTAIN
    assert res.pest_validation.original_model_score is None
    assert res.pest_validation.diagnostic_status == DiagnosticStatus.UNCERTAIN
    assert "Missing confidence score" in res.crop_validation.warnings[0]


# =====================================================================
# 11. INVALID, MISSING, OR UNAVAILABLE MODEL WEIGHTS
# =====================================================================
def test_11_unavailable_model_weights(engine):
    pest_data = {
        "status": "MODEL_UNAVAILABLE",
        "is_operational": False,
        "detected_pests": [],
        "primary_pest": None,
    }
    weed_data = {
        "status": "MODEL_UNAVAILABLE",
        "is_operational": False,
        "detected_weeds": [],
    }
    res = engine.validate(
        crop_data={"crop_name": "Potato", "confidence": 0.85},
        disease_data={"status": "NO_DISEASE_DETECTED"},
        pest_data=pest_data,
        weed_data=weed_data,
    )
    assert res.pest_validation.diagnostic_status == DiagnosticStatus.UNABLE_TO_ASSESS
    assert res.weed_validation.diagnostic_status == DiagnosticStatus.UNABLE_TO_ASSESS
    assert res.pest_validation.diagnostic_status != DiagnosticStatus.NOT_DETECTED
    assert res.weed_validation.diagnostic_status != DiagnosticStatus.NOT_DETECTED


# =====================================================================
# 12. POOR-QUALITY AND INVALID IMAGES
# =====================================================================
def test_12_poor_quality_and_invalid_images(engine):
    # Blur score < 12.0
    quality = {"is_valid": True, "blur_score": 8.4, "errors": []}
    res = engine.validate(
        crop_data={"crop_name": "Potato", "confidence": 0.85},
        disease_data={"status": "CONFIRMED", "disease_name": "Late blight", "confidence": 0.85},
        pest_data={"status": "CONFIRMED", "primary_pest": "Aphids", "confidence": 0.85},
        weed_data={"status": "NO_WEED_DETECTED"},
        image_quality_data=quality,
    )
    assert any(c.code == "POOR_IMAGE_QUALITY" for c in res.detected_contradictions)
    assert res.crop_validation.diagnostic_status == DiagnosticStatus.UNABLE_TO_ASSESS
    assert res.disease_validation.diagnostic_status == DiagnosticStatus.UNABLE_TO_ASSESS
    assert res.pest_validation.diagnostic_status == DiagnosticStatus.UNABLE_TO_ASSESS


# =====================================================================
# 13. DISEASE AND INSECT PREDICTIONS THAT DISAGREE
# =====================================================================
def test_13_disease_and_insect_disagreement(engine):
    disease_data = {
        "disease_name": "Fungal Downy Mildew",
        "confidence": 0.85,
        "status": "CONFIRMED",
    }
    pest_data = {
        "primary_pest": "Asiatic Rice Borer",
        "confidence": 0.85,
        "status": "CONFIRMED",
        "is_operational": True,
        "detected_pests": [{"pest_name": "Asiatic Rice Borer", "confidence": 0.85}],
    }
    res = engine.validate(
        crop_data={"crop_name": "Rice / Paddy", "confidence": 0.90},
        disease_data=disease_data,
        pest_data=pest_data,
        weed_data={"status": "NO_WEED_DETECTED"},
    )
    assert len(res.warnings) > 0
    # Both hypotheses are preserved independently
    assert res.disease_validation.predicted_label == "Fungal Downy Mildew"
    assert res.pest_validation.predicted_label == "Asiatic Rice Borer"


# =====================================================================
# 14. NO DISEASE DETECTED DOES NOT FALSELY DECLARE PLANT HEALTHY
# =====================================================================
def test_14_no_disease_detected_independence(engine):
    disease_data = {
        "status": "NO_DISEASE_DETECTED",
        "disease_name": "No Disease Detected",
        "confidence": 0.0,
    }
    res = engine.validate(
        crop_data={"crop_name": "Potato", "confidence": 0.85},
        disease_data=disease_data,
        pest_data={"status": "NO_PEST_DETECTED"},
        weed_data={"status": "NO_WEED_DETECTED"},
    )
    assert res.disease_validation.diagnostic_status == DiagnosticStatus.NOT_DETECTED
    assert "does not prove absolute absence" in res.disease_validation.evidence_summary.lower()


# =====================================================================
# 15. NO WEED DETECTED DOES NOT DECLARE FIELD WEED-FREE
# =====================================================================
def test_15_no_weed_detected_independence(engine):
    weed_data = {
        "status": "NO_WEED_DETECTED",
        "confidence": 0.0,
        "detected_weeds": [],
    }
    res = engine.validate(
        crop_data={"crop_name": "Potato", "confidence": 0.85},
        disease_data={"status": "NO_DISEASE_DETECTED"},
        pest_data={"status": "NO_PEST_DETECTED"},
        weed_data=weed_data,
    )
    assert res.weed_validation.diagnostic_status == DiagnosticStatus.NOT_DETECTED
    assert "does not prove that the entire plant or agricultural field is weed-free" in res.weed_validation.evidence_summary.lower()


# =====================================================================
# 16. GEMINI ROUTING REQUESTED WHILE GEMINI IS DISABLED
# =====================================================================
def test_16_gemini_routing_disabled_by_default(engine):
    crop_data = {"crop_name": "Potato", "confidence": 0.35, "status": "UNCERTAIN"}
    pest_data = {"primary_pest": "Colorado Potato Beetle", "confidence": 0.50, "status": "UNCERTAIN"}
    res = engine.validate(
        crop_data=crop_data,
        disease_data={"status": "NO_DISEASE_DETECTED"},
        pest_data=pest_data,
        weed_data={"status": "NO_WEED_DETECTED"},
    )
    routing = res.verification_routing
    assert routing.verification_required is True
    assert routing.gemini_feature_enabled is False
    assert routing.gemini_routing_status == "DISABLED"
    assert "disabled by configuration in this phase" in routing.gemini_action_summary
    assert len(routing.triggers) > 0


# =====================================================================
# 17. PRESERVATION OF ORIGINAL MODEL PREDICTIONS
# =====================================================================
def test_17_preservation_of_original_predictions(engine):
    crop_data = {"crop_name": "Potato", "confidence": 0.44}
    disease_data = {"disease_name": "Early Blight", "confidence": 0.62, "status": "UNCERTAIN"}
    pest_data = {
        "primary_pest": "Colorado Potato Beetle",
        "confidence": 0.77,
        "status": "CONFIRMED",
        "detected_pests": [{"pest_name": "Colorado Potato Beetle", "confidence": 0.77}],
    }
    weed_data = {
        "status": "CONFIRMED",
        "confidence": 0.81,
        "detected_weeds": [{"weed_name": "Purple Nutsedge", "confidence": 0.81}],
    }
    res = engine.validate(crop_data, disease_data, pest_data, weed_data)

    assert res.crop_validation.predicted_label == "Potato"
    assert res.crop_validation.original_model_score == 0.44
    assert res.disease_validation.predicted_label == "Early Blight"
    assert res.disease_validation.original_model_score == 0.62
    assert res.pest_validation.predicted_label == "Colorado Potato Beetle"
    assert res.pest_validation.original_model_score == 0.77
    assert res.weed_validation.predicted_label == "Purple Nutsedge"
    assert res.weed_validation.original_model_score == 0.81


# =====================================================================
# 18. PREVENTION OF CROP-LABEL CHANGES BASED SOLELY ON HOST-PEST
# =====================================================================
def test_18_prevention_of_crop_label_alteration(engine):
    # Predict Potato with 35%, and Bean Leaf Beetle with 85%
    crop_data = {"crop_name": "Potato", "confidence": 0.35, "status": "UNCERTAIN"}
    pest_data = {
        "primary_pest": "Bean Leaf Beetle",
        "confidence": 0.85,
        "status": "CONFIRMED",
        "detected_pests": [{"pest_name": "Bean Leaf Beetle", "confidence": 0.85}],
    }
    res = engine.validate(
        crop_data=crop_data,
        disease_data={"status": "NO_DISEASE_DETECTED"},
        pest_data=pest_data,
        weed_data={"status": "NO_WEED_DETECTED"},
    )
    # CRITICAL: Crop must NOT become "Beans" or "Soybean"
    assert res.crop_validation.predicted_label == "Potato"
    # Insect must NOT be replaced with Colorado Potato Beetle
    assert res.pest_validation.predicted_label == "Bean Leaf Beetle"


# =====================================================================
# 19. PREVENTION OF ONE CATEGORY CONTAMINATING ANOTHER
# =====================================================================
def test_19_prevention_of_category_contamination(engine):
    # Pl@ntNet disease stream returns non-pathology insect
    disease_data = {
        "status": "INVALID_CATEGORY",
        "disease_name": "None (Arthropod/Insect Pest in Stream)",
        "raw_provider_finding": "Leptinotarsa decemlineata - Colorado beetle",
        "raw_provider_score": 0.65,
    }
    res = engine.validate(
        crop_data={"crop_name": "Potato", "confidence": 0.85},
        disease_data=disease_data,
        pest_data={"status": "NO_PEST_DETECTED"},
        weed_data={"status": "NO_WEED_DETECTED"},
    )
    # Disease must NOT adopt insect name as pathology
    assert "Colorado" not in res.disease_validation.predicted_label
    assert res.disease_validation.diagnostic_status == DiagnosticStatus.NOT_DETECTED
    assert any(c.code == "NON_PATHOLOGY_IN_DISEASE_STREAM" for c in res.detected_contradictions)


# =====================================================================
# 20. REGRESSION TESTS FOR EXISTING PHASE 1 DISEASE PIPELINE
# =====================================================================
def test_20_regression_phase1_disease_detection_pipeline():
    # Verify existing validate_diagnosis_evidence continues to work
    val_res = OverallImageValidationResult(
        total_submitted=1,
        valid_count=1,
        invalid_count=0,
        is_any_valid=True,
        details=[ImageValidationDetail(
            filename="leaf.jpg",
            is_valid=True,
            size_bytes=1000,
            blur_score=45.0,
            brightness=120.0,
            errors=[],
            warnings=[],
        )],
    )
    crop_info = CropIdentificationResult(
        crop_name="Tomato",
        confidence=1.0,
        source="user_selected",
        status="USER_SPECIFIED",
        evidence_note="Specified by user",
    )
    disease_res = NormalizedDiseaseResult(
        disease_name="Early blight (Alternaria solani)",
        category="FUNGAL",
        confidence=0.92,
        provider_name="Pl@ntNet Diseases API",
        is_mock=False,
        supported=True,
        candidates=[],
        provider_status="OK",
    )
    diag = validate_diagnosis_evidence(val_res, crop_info, disease_res)
    assert diag.diagnosis_status == "CONFIRMED"
    assert diag.evidence_level == "HIGH"
    assert diag.is_uncertain is False
    assert diag.calibrated_confidence > 0.70


# =====================================================================
# 21. FULL REGRESSION: POTATO VS BEAN BEETLE INDEPENDENT ADJUDICATION
# =====================================================================
def test_21_potato_vs_bean_beetle_regression_and_adjudication(engine):
    """
    Validates Phase 4 Potato-vs-Bean regression test:
      - Crop: Potato @ 26.6% (Low confidence tail score from PlantNet)
      - Pest: Colorado Potato Beetle @ 76.7% (Uncalibrated consensus promotion)
      - Disease: Non-pathology organism in EPPO stream
      - Weed: No weed detected in macro frame
    Verifies that:
      1. Crop is marked UNCERTAIN; original score 0.266 is preserved.
      2. Pest is demoted from CONFIRMED to NEEDS_VERIFICATION due to low crop confidence.
      3. Antigravity independent assessment identifies ambiguity between Solanaceous and Fabaceous leaflets.
      4. Antigravity identifies Chrysomelid beetle morphology with competing species (CPB vs BLB vs Hadda).
      5. Structured category comparisons document IP102 limitations (neither CPB nor BLB in 102 classes).
      6. Conditional Gemini verification query is generated with targeted morphological questions.
      7. Final adjudication report preserves uncertainty and recommends specific agronomist follow-up.
    """
    crop_data = {
        "crop_name": "Potato",
        "scientific_name": "Solanum tuberosum",
        "confidence": 0.266,
        "status": "UNCERTAIN",
        "is_operational": True,
    }
    disease_data = {
        "disease_name": "No Disease Detected",
        "status": "NO_DISEASE_DETECTED",
        "raw_provider_finding": "Leptinotarsa decemlineata - Colorado beetle (Colorado potato beetle)",
        "raw_provider_score": 0.464,
        "is_non_pathology": True,
        "is_operational": True,
    }
    pest_data = {
        "primary_pest": "Colorado Potato Beetle",
        "scientific_name": "Leptinotarsa decemlineata",
        "confidence": 0.767,
        "status": "CONFIRMED",
        "is_operational": True,
        "detected_pests": [
            {
                "pest_name": "Colorado Potato Beetle",
                "scientific_name": "Leptinotarsa decemlineata",
                "confidence": 0.767,
                "pest_class_id": 68,
            }
        ],
    }
    weed_data = {
        "status": "NO_WEED_DETECTED",
        "confidence": 0.0,
        "is_operational": True,
        "detected_weeds": [],
    }

    res = engine.validate(
        crop_data=crop_data,
        disease_data=disease_data,
        pest_data=pest_data,
        weed_data=weed_data,
    )

    # 1. Preserved raw scores and calibrated statuses
    assert res.crop_validation.predicted_label == "Potato"
    assert res.crop_validation.original_model_score == 0.266
    assert res.crop_validation.diagnostic_status == DiagnosticStatus.UNCERTAIN

    assert res.pest_validation.predicted_label == "Colorado Potato Beetle"
    assert res.pest_validation.original_model_score == 0.767
    # Demoted from CONFIRMED because crop confidence is low (< 70%)
    assert res.pest_validation.diagnostic_status == DiagnosticStatus.NEEDS_VERIFICATION

    # 2. Antigravity Independent Assessment
    assert res.antigravity_assessment is not None
    ag = res.antigravity_assessment
    assert "Fabaceae" in ag.crop.primary_candidate or "Solanaceae" in ag.crop.primary_candidate
    assert ag.crop.suitable_for_confirmation is False
    assert "Chrysomelidae" in ag.pest.primary_candidate
    assert any("Cerotoma" in c for c in ag.pest.alternative_candidates)
    assert any("Leptinotarsa" in c for c in ag.pest.alternative_candidates)
    assert ag.pest.suitable_for_confirmation is False
    assert ag.disease.suitable_for_confirmation is True  # True that no active foliar pathology is present

    # 3. Category Comparisons
    assert len(res.category_comparisons) == 5
    pest_comp = next(c for c in res.category_comparisons if c.category == "pest")
    assert any("102" in lim for lim in pest_comp.known_model_limitations or [])
    assert pest_comp.requires_expert_review is True

    # 4. Conditional Gemini Query
    assert res.conditional_gemini_query is not None
    assert res.conditional_gemini_query.triggered is True
    assert len(res.conditional_gemini_query.targeted_questions) >= 3
    prompt_lower = res.conditional_gemini_query.prompt_text.lower()
    assert "elytra" in prompt_lower or "stripes" in prompt_lower
    assert "potato" in prompt_lower

    # 5. Final Adjudication Report
    assert res.final_adjudication_report is not None
    rep = res.final_adjudication_report
    assert rep.best_supported_crop["status"] == "UNCERTAIN"
    assert rep.best_supported_pest["status"] == "NEEDS_VERIFICATION"
    assert len(rep.further_actions_needed) >= 2


