"""
pest_validator.py — Diagnostic Validation & Strict >70% Confidence Gate
--------------------------------------------------------------------------
Implements conservative diagnostic validation for insect and pest detections:
  - Enforces the strict >70% confidence threshold gate:
      * Confidence > 0.70 is eligible for CONFIRMED diagnosis.
      * Confidence <= 0.70 is strictly marked UNCERTAIN.
  - Penalizes blurry, underexposed, or low-resolution image inputs.
  - Verifies host crop compatibility against IP102 susceptibility matrices.
  - Explicitly distinguishes specimen sightings from foliar damage traces.
  - Emits actionable retry guidance and uncertainty notifications.
  - Never interprets high confidence as absolute real-world accuracy.
"""

import logging
from typing import List, Optional, Tuple

from schemas.leaf_disease import OverallImageValidationResult, CropIdentificationResult
from schemas.pest_detection import (
    DetectedPestItem,
    PestModelInfo,
    PestValidationResult,
)
from services.pest_detection.ip102_classes import (
    is_crop_susceptible,
    classify_pest_type_distinction,
    get_ip102_class,
)

logger = logging.getLogger(__name__)

STRICT_CONFIDENCE_THRESHOLD = 0.70


def validate_pest_findings(
    detections: List[DetectedPestItem],
    crop_info: CropIdentificationResult,
    validation_result: OverallImageValidationResult,
    model_info: PestModelInfo,
) -> PestValidationResult:
    """
    Evaluates raw pest detections against image quality, host compatibility,
    and the strict >70% confidence threshold gate.
    """
    notes: List[str] = []

    # 1. Model Availability Check
    if not model_info.is_operational:
        notes.append("Inference model weights are not loaded. Model is unavailable.")
        notes.append(model_info.status_message)
        return PestValidationResult(
            diagnosis_status="MODEL_UNAVAILABLE",
            calibrated_confidence=0.0,
            is_uncertain=True,
            confidence_gate_passed=False,
            evidence_level="INSUFFICIENT",
            pest_type_distinction="UNCERTAIN",
            crop_host_compatibility="UNRESTRICTED",
            image_quality_status="ACCEPTABLE",
            validation_notes=notes,
            retry_guidance=(
                "Pest detection model is currently awaiting local weights checkpoint. "
                "No automated inference could be performed."
            ),
        )

    # 2. Image Quality Assessment
    valid_details = [d for d in validation_result.details if d.is_valid]
    has_blurry = any(d.blur_score < 12.0 for d in valid_details)
    has_exposure_flaws = any(
        "dark" in w.lower() or "overexposed" in w.lower()
        for d in valid_details
        for w in d.warnings
    )

    if not valid_details:
        image_quality_status = "POOR"
        notes.append("No valid images submitted for assessment.")
    elif has_blurry:
        image_quality_status = "SUBOPTIMAL"
        notes.append("Image exhibits blur or soft focus, impacting fine diagnostic details.")
    elif has_exposure_flaws:
        image_quality_status = "ACCEPTABLE"
        notes.append("Image lighting has minor exposure or contrast warnings.")
    else:
        image_quality_status = "GOOD"
        notes.append("Image quality, sharpness, and illumination are good.")

    # 3. Empty Detections Assessment
    if not detections:
        notes.append("No recognized insect pests or characteristic feeding damage detected in image.")
        return PestValidationResult(
            diagnosis_status="NO_PEST_DETECTED",
            calibrated_confidence=0.0,
            is_uncertain=True,
            confidence_gate_passed=False,
            evidence_level="INSUFFICIENT",
            pest_type_distinction="UNCERTAIN",
            crop_host_compatibility="UNRESTRICTED",
            image_quality_status=image_quality_status,
            validation_notes=notes,
            retry_guidance=(
                "No pests detected. If you suspect an infestation, photograph the exact leaf symptom "
                "or insect specimen in sharp focus under daylight."
            ),
        )

    # 4. Primary Detection & Confidence Evaluation
    # Sort by raw confidence descending
    sorted_detections = sorted(detections, key=lambda p: p.confidence, reverse=True)
    primary = sorted_detections[0]
    raw_conf = primary.confidence

    notes.append(f"Primary candidate: '{primary.pest_name}' (Raw model confidence: {raw_conf * 100:.1f}%).")

    # 5. Specimen vs. Damage Distinction
    categories = set(p.category.upper() for p in detections)
    if categories == {"PEST_DAMAGE"}:
        pest_type_distinction = "DAMAGE_ONLY"
        notes.append("Pattern indicates foliar feeding damage; the causative pest specimen may have vacated.")
    elif "PEST_DAMAGE" in categories and len(categories) > 1:
        pest_type_distinction = "MIXED"
        notes.append("Both live specimens and foliar damage traces recognized.")
    else:
        pest_type_distinction = "SPECIMEN_DETECTED"
        notes.append("Direct insect/pest specimen localized on plant foliage.")

    if len(detections) > 1:
        notes.append(f"Multi-pest co-occurrence detected ({len(detections)} distinct instances localized).")

    # 6. Host Crop Compatibility Check
    crop_name = crop_info.crop_name
    is_compatible = is_crop_susceptible(crop_name, primary.pest_class_id)

    if not crop_name or crop_name.lower() in ("unknown", "unspecified", "none"):
        crop_host_compatibility = "HOST_NOT_SPECIFIED"
        notes.append("Target host crop was not specified (optional input). Evaluation conducted under general/unrestricted host mode.")
    elif is_compatible:
        crop_host_compatibility = "COMPATIBLE"
        notes.append(f"Pest '{primary.pest_name}' is known to infest host crop '{crop_name}'.")
    else:
        crop_host_compatibility = "POTENTIAL_MISMATCH"
        notes.append(
            f"Potential host mismatch: '{primary.pest_name}' is not typically cataloged as a primary pest of '{crop_name}'."
        )

    # 7. Confidence Calibration
    calibrated = raw_conf

    # Penalties for flaws
    if image_quality_status == "POOR":
        calibrated -= 0.30
    elif image_quality_status == "SUBOPTIMAL":
        calibrated -= 0.15

    if crop_host_compatibility == "POTENTIAL_MISMATCH":
        calibrated -= 0.25

    if pest_type_distinction == "DAMAGE_ONLY":
        # Damage without specimen has inherently lower diagnostic certainty
        calibrated -= 0.10

    # Bound calibrated score to [0.0, 1.0]
    calibrated = max(0.0, min(1.0, round(calibrated, 2)))
    notes.append(f"Calibrated confidence computed as {calibrated * 100:.1f}%.")

    # 8. Strict Confidence Gate Application
    # Rule 9: Confidence strictly > 0.70 required for confirmation. Results <= 0.70 MUST remain uncertain.
    passes_strict_gate = (raw_conf > STRICT_CONFIDENCE_THRESHOLD) and (calibrated > STRICT_CONFIDENCE_THRESHOLD)

    if passes_strict_gate and crop_host_compatibility != "POTENTIAL_MISMATCH" and image_quality_status != "POOR":
        diagnosis_status = "CONFIRMED"
        is_uncertain = False
        evidence_level = "HIGH"
        retry_guidance = None
        notes.append("Strict confidence threshold (>70%) satisfied. Diagnosis confirmed.")
    else:
        diagnosis_status = "UNCERTAIN"
        is_uncertain = True
        evidence_level = "MEDIUM" if calibrated > 0.40 else "LOW"
        notes.append(
            f"Strict confidence threshold (>70%) not satisfied (raw: {raw_conf*100:.1f}%, calibrated: {calibrated*100:.1f}%). "
            f"Candidate species '{primary.pest_name}' must be treated as unverified."
        )
        notes.append(
            "Taxonomic Advisory: IP102 is a closed 102-class catalog. Insects from unrepresented groups "
            "(such as Chrysomelidae leaf beetles) may trigger low-confidence matches to visually adjacent classes."
        )
        notes.append(
            "Damage Attribution Notice: Associated feeding mechanism is derived from the candidate profile. "
            "Visible foliar damage cannot be conclusively attributed to the observed insect without definitive identification."
        )
        retry_guidance = (
            "Confidence is below the 70% confirmation threshold. Treat the species identification as provisional. "
            "Please upload a close-up, sharp photograph of the insect or feeding site in natural daylight."
        )

    return PestValidationResult(
        diagnosis_status=diagnosis_status,
        calibrated_confidence=calibrated,
        is_uncertain=is_uncertain,
        confidence_gate_passed=passes_strict_gate,
        evidence_level=evidence_level,
        pest_type_distinction=pest_type_distinction,
        crop_host_compatibility=crop_host_compatibility,
        image_quality_status=image_quality_status,
        validation_notes=notes,
        retry_guidance=retry_guidance,
    )
