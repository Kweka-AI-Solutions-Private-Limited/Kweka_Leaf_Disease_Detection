"""
test_hybrid_pest_consensus.py — Unit Tests for Hybrid Insect Consensus Engine
--------------------------------------------------------------------------------
Validates:
  1. Mutual corroboration between Local YOLO and EPPO stream (Bayesian fusion > 70% promotion).
  2. Preservation of spatial bounding boxes from the local detector.
  3. Strict retention of UNCERTAIN status when both models are < 70% without corroboration.
  4. Conflict handling when models suggest contradictory pest groups.
  5. High confidence preservation when local detector is independently > 70%.
"""

import sys
from pathlib import Path
import pytest

_src_dir = str(Path(__file__).resolve().parent.parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from schemas.unified_test import (
    PestDetectionTestResult,
    DetectedPestTestItem,
    PestBoundingBoxTestItem,
    DiseaseDetectionTestResult,
    CropIdentificationTestResult,
)
from services.pest_detection.pest_consensus import reconcile_hybrid_pest_detection


def test_mutual_corroboration_promotes_uncertain_to_confirmed():
    # Model A: Local YOLO detected beetle morphology at 47.2% with bounding box
    bbox = PestBoundingBoxTestItem(ymin=0.28, xmin=0.22, ymax=0.58, xmax=0.57, label="Beetle", confidence=0.472)
    local_pest = PestDetectionTestResult(
        status="UNCERTAIN",
        detected_pests=[
            DetectedPestTestItem(
                pest_name="Tiger Longicorn Beetle / Stem Borer (Xylotrechus)",
                scientific_name="Xylotrechus quadripes",
                pest_class_id=68,
                category="INSECT",
                confidence=0.472,
                damage_type="stem_boring",
                bounding_box=bbox,
            )
        ],
        primary_pest="Tiger Longicorn Beetle / Stem Borer (Xylotrechus)",
        confidence=0.472,
        confidence_gate_passed=False,
        provider="IP102 YOLO Detector",
        is_operational=True,
        model_name="IP102 Detector",
        message="Candidate insect pest at 47.2% confidence.",
    )

    # Model B: EPPO pathology stream detected Colorado beetle at 46.4%
    disease_res = DiseaseDetectionTestResult(
        status="INVALID_CATEGORY",
        disease_name="Colorado beetle (Leptinotarsa decemlineata)",
        common_name="Colorado beetle",
        scientific_name="Leptinotarsa decemlineata",
        confidence=0.464,
        confidence_gate_passed=False,
        provider="Pl@ntNet EPPO",
        is_operational=True,
        raw_provider_finding="Colorado beetle (Leptinotarsa decemlineata)",
        raw_provider_score=0.464,
        category_warning="Non-pathology organism excluded.",
        message="Non-pathology insect detected in pathology stream.",
    )

    # Context: Host crop is Potato
    crop_res = CropIdentificationTestResult(
        status="CONFIRMED",
        crop_name="Potato",
        scientific_name="Solanum tuberosum",
        confidence=0.92,
        is_agricultural_crop=True,
        plant_type="CULTIVATED_CROP",
        provider="Pl@ntNet Botanical",
        is_operational=True,
        message="Confirmed crop: Potato",
    )

    fused = reconcile_hybrid_pest_detection(local_pest, disease_res, crop_res)

    # Verifications
    assert fused.status == "CONFIRMED"
    assert fused.confidence_gate_passed is True
    assert fused.confidence > 0.70  # Bayesian fusion boosts beyond the 70% threshold
    assert fused.consensus_applied is True
    assert fused.cross_model_verified is True
    assert fused.primary_pest == "Colorado Potato Beetle"

    # Crucial: Preserves local bounding box
    assert len(fused.detected_pests) == 1
    top_item = fused.detected_pests[0]
    assert top_item.bounding_box is not None
    assert top_item.bounding_box.ymin == 0.28
    assert top_item.bounding_box.xmin == 0.22
    assert "Leptinotarsa decemlineata" in (top_item.scientific_name or "")


def test_both_models_under_70_without_corroboration_remains_uncertain():
    # Local YOLO detected a stem borer at 42%
    local_pest = PestDetectionTestResult(
        status="UNCERTAIN",
        detected_pests=[
            DetectedPestTestItem(
                pest_name="Stem Borer",
                scientific_name="Chilo suppressalis",
                pest_class_id=10,
                category="INSECT",
                confidence=0.42,
                damage_type="stem_boring",
                bounding_box=None,
            )
        ],
        primary_pest="Stem Borer",
        confidence=0.42,
        confidence_gate_passed=False,
        provider="IP102 YOLO Detector",
        is_operational=True,
        model_name="IP102 Detector",
        message="Candidate at 42.0% confidence.",
    )

    # Disease stream has a botanical fungus, NOT an insect
    disease_res = DiseaseDetectionTestResult(
        status="UNCERTAIN",
        disease_name="Early Blight",
        common_name="Early Blight",
        scientific_name="Alternaria solani",
        confidence=0.45,
        confidence_gate_passed=False,
        provider="Pl@ntNet EPPO",
        is_operational=True,
        raw_provider_finding="Alternaria solani",
        raw_provider_score=0.45,
        message="Early blight candidate.",
    )

    crop_res = CropIdentificationTestResult(
        status="CONFIRMED",
        crop_name="Tomato",
        confidence=0.88,
        is_agricultural_crop=True,
        plant_type="CULTIVATED_CROP",
        provider="Pl@ntNet",
        is_operational=True,
        message="Confirmed crop: Tomato",
    )

    fused = reconcile_hybrid_pest_detection(local_pest, disease_res, crop_res)

    # Must remain UNCERTAIN, no ungrounded boost
    assert fused.status == "UNCERTAIN"
    assert fused.confidence_gate_passed is False
    assert fused.confidence == 0.42
    assert fused.cross_model_verified is False


def test_conflicting_models_retains_uncertainty_with_explanation():
    # Model A says Caterpillar at 52%
    local_pest = PestDetectionTestResult(
        status="UNCERTAIN",
        detected_pests=[
            DetectedPestTestItem(
                pest_name="Armyworm Caterpillar",
                scientific_name="Spodoptera frugiperda",
                pest_class_id=5,
                category="INSECT",
                confidence=0.52,
                damage_type="foliar_chewing",
                bounding_box=None,
            )
        ],
        primary_pest="Armyworm Caterpillar",
        confidence=0.52,
        confidence_gate_passed=False,
        provider="IP102 YOLO Detector",
        is_operational=True,
        model_name="IP102 Detector",
        message="Candidate at 52.0% confidence.",
    )

    # Model B says Beetle at 48% on Wheat
    disease_res = DiseaseDetectionTestResult(
        status="INVALID_CATEGORY",
        disease_name="Colorado beetle",
        confidence=0.48,
        confidence_gate_passed=False,
        provider="Pl@ntNet EPPO",
        is_operational=True,
        raw_provider_finding="Colorado beetle (Leptinotarsa decemlineata)",
        raw_provider_score=0.48,
        message="Insect detected.",
    )

    crop_res = CropIdentificationTestResult(
        status="CONFIRMED",
        crop_name="Wheat",
        confidence=0.85,
        is_agricultural_crop=True,
        plant_type="CULTIVATED_CROP",
        provider="Pl@ntNet",
        is_operational=True,
        message="Confirmed crop: Wheat",
    )

    fused = reconcile_hybrid_pest_detection(local_pest, disease_res, crop_res)

    assert fused.status == "UNCERTAIN"
    assert fused.confidence_gate_passed is False
    assert "Conflicting" in fused.message


def test_high_confidence_local_yolo_is_preserved():
    # Local YOLO is independently high confidence (85%)
    bbox = PestBoundingBoxTestItem(ymin=0.1, xmin=0.1, ymax=0.5, xmax=0.5, label="Fall Armyworm", confidence=0.85)
    local_pest = PestDetectionTestResult(
        status="CONFIRMED",
        detected_pests=[
            DetectedPestTestItem(
                pest_name="Fall Armyworm",
                scientific_name="Spodoptera frugiperda",
                pest_class_id=1,
                category="INSECT",
                confidence=0.85,
                damage_type="foliar_chewing",
                bounding_box=bbox,
            )
        ],
        primary_pest="Fall Armyworm",
        confidence=0.85,
        confidence_gate_passed=True,
        provider="IP102 YOLO Detector",
        is_operational=True,
        model_name="IP102 Detector",
        message="Confirmed insect pest with 85% confidence.",
    )

    disease_res = DiseaseDetectionTestResult(
        status="NO_DISEASE_DETECTED",
        disease_name="None",
        confidence=0.0,
        confidence_gate_passed=False,
        provider="Pl@ntNet EPPO",
        is_operational=True,
        message="No disease.",
    )

    fused = reconcile_hybrid_pest_detection(local_pest, disease_res, None)

    assert fused.status == "CONFIRMED"
    assert fused.confidence == 0.85
    assert fused.confidence_gate_passed is True
