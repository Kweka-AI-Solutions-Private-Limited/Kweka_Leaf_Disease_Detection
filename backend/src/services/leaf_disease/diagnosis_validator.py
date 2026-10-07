"""
diagnosis_validator.py — Evidence Evaluation & Diagnosis Validation Layer (Phase 1-5)
-------------------------------------------------------------------------------------
Evaluates detection evidence based on:
  - Raw model confidence vs visual evidence compatibility
  - Symptom morphology & contradiction detection (e.g. Fungal vs Cottony/Pest)
  - Host-pathogen compatibility constraints
  - Image quality (blur, resolution, lighting)
  - Calibrated evidence-aware confidence calculation

Classifies evidence into HIGH, MEDIUM, or LOW and enforces uncertainty gating.
"""

import logging
from typing import List, Optional, Tuple
from schemas.leaf_disease import (
    OverallImageValidationResult,
    CropIdentificationResult,
    NormalizedDiseaseResult,
    DiagnosisValidationResult,
)

logger = logging.getLogger(__name__)

PATHOGEN_HOST_MAP = {
    "podosphaera xanthii": ["cucurbits", "cucumber", "melon", "squash", "pumpkin", "gourd"],
    "golovinomyces cichoracearum": ["cucurbits", "cucumber", "melon", "squash", "pumpkin", "gourd"],
    "erysiphe necator": ["grape"],
    "uncinula necator": ["grape"],
    "gymnosporangium sabinae": ["pear"],
    "gymnosporangium juniperi-virginianae": ["apple"],
}

# Keywords signaling cottony / scale / pest visual evidence
PEST_COTTONY_KEYWORDS = ["cottony", "waxy", "scale", "mealybug", "axil", "mass", "whitefly", "aphid", "webbing", "exuviae"]
FUNGAL_LESION_KEYWORDS = ["spot", "blight", "rot", "rust", "anthracnose", "scab", "mildew", "canker"]


def _check_host_compatibility(crop_name: str, disease_name: str) -> Optional[bool]:
    """
    Returns True if compatible, False if host-pathogen mismatch, or None if no obligate host constraint exists.
    """
    if not crop_name or not disease_name:
        return None

    disease_lower = disease_name.lower()
    crop_lower = crop_name.lower()

    for pathogen_key, valid_hosts in PATHOGEN_HOST_MAP.items():
        if pathogen_key in disease_lower:
            is_valid_host = any(vh in crop_lower for vh in valid_hosts)
            return is_valid_host

    return None


def detect_evidence_contradiction(
    disease_result: NormalizedDiseaseResult
) -> Tuple[bool, List[str]]:
    """
    Checks for structural contradiction between the selected disease diagnosis and observable visual evidence.
    Example: Fungal pathogen selected when visible evidence describes white/cottony/waxy deposits at axils.
    """
    contradictions = []
    category = (disease_result.category or "UNKNOWN_UNCERTAIN").upper()
    disease_name_lower = (disease_result.disease_name or "").lower()
    
    ve = disease_result.visual_evidence
    visible_texts = []
    if ve and ve.directly_visible:
        visible_texts.extend([t.lower() for t in ve.directly_visible])
    if ve and ve.dominant_morphology:
        visible_texts.append(ve.dominant_morphology.lower())

    combined_evidence = " ".join(visible_texts)

    has_cottony_pest_evidence = any(kw in combined_evidence for kw in PEST_COTTONY_KEYWORDS)
    is_fungal_diagnosis = category == "FUNGAL" or any(kw in disease_name_lower for kw in FUNGAL_LESION_KEYWORDS)

    if is_fungal_diagnosis and has_cottony_pest_evidence:
        contradictions.append(
            "Visual evidence describes white/cottony/waxy structures or pest morphology, but primary diagnosis is a fungal disease."
        )

    return (len(contradictions) > 0, contradictions)


def calibrate_confidence(
    raw_confidence: Optional[float],
    category: str,
    image_quality_status: str,
    crop_compatibility_status: str,
    contradiction_found: bool,
    has_visual_evidence: bool
) -> float:
    """
    Calculates calibrated confidence score (0.0 to 1.0) reflecting evidence alignment rather than trusting raw model score.
    """
    base = raw_confidence if raw_confidence is not None else 0.50

    # Contradiction penalty
    if contradiction_found:
        base -= 0.45
        logger.info("Calibrated confidence penalized for evidence contradiction (-0.45)")

    # Host mismatch penalty
    if crop_compatibility_status == "MISMATCHED_HOST":
        base -= 0.50

    # Image quality penalty
    if image_quality_status == "POOR":
        base -= 0.35
    elif image_quality_status == "SUBOPTIMAL":
        base -= 0.15

    # Crop uncertain penalty
    if crop_compatibility_status == "UNCERTAIN":
        base -= 0.10

    # Category uncertain penalty
    if category in ("UNKNOWN_UNCERTAIN", "UNKNOWN"):
        base -= 0.20

    # Boost for direct visual evidence alignment
    if has_visual_evidence and not contradiction_found and image_quality_status == "GOOD":
        base += 0.05

    return max(0.0, min(1.0, round(base, 2)))


def validate_diagnosis_evidence(
    validation_result: OverallImageValidationResult,
    crop_info: CropIdentificationResult,
    disease_result: NormalizedDiseaseResult
) -> DiagnosisValidationResult:
    """
    Evaluates evidence factors conservatively and produces calibrated confidence and evidence level.
    Generates targeted close-up requests for ambiguous or low-quality cases.
    """
    notes: List[str] = []

    # 1. Image Quality Evaluation
    valid_details = [d for d in validation_result.details if d.is_valid]
    has_blurry = any(d.blur_score < 25.0 for d in valid_details)
    has_exposure_warnings = any("dark" in w.lower() or "overexposed" in w.lower() for d in valid_details for w in d.warnings)

    if not valid_details:
        image_quality_status = "POOR"
        notes.append("No valid images available for assessment.")
    elif has_blurry:
        image_quality_status = "SUBOPTIMAL"
        notes.append("Some images exhibit blur or softness.")
    elif has_exposure_warnings:
        image_quality_status = "ACCEPTABLE"
        notes.append("Image lighting/exposure is acceptable but suboptimal.")
    else:
        image_quality_status = "GOOD"
        notes.append("Image quality and clarity are good.")

    # 2. Host-Pathogen Compatibility Check
    host_compat = _check_host_compatibility(crop_info.crop_name, disease_result.disease_name)

    if host_compat is False:
        crop_compatibility_status = "MISMATCHED_HOST"
        notes.append(
            f"Host-pathogen mismatch detected: Pathogen '{disease_result.disease_name}' "
            f"is incompatible with crop '{crop_info.crop_name}'."
        )
    elif crop_info.status in ("CONFIRMED", "USER_SPECIFIED"):
        crop_compatibility_status = "COMPATIBLE"
        notes.append(f"Crop '{crop_info.crop_name}' verified ({crop_info.status}).")
    else:
        crop_compatibility_status = "UNCERTAIN"
        notes.append("Crop identification is uncertain.")

    # 3. Multi-image Consistency Evaluation
    if validation_result.valid_count > 1:
        consistency_status = "CONSISTENT"
        notes.append(f"Analysis consistent across {validation_result.valid_count} submitted images.")
    else:
        consistency_status = "SINGLE_IMAGE"
        notes.append("Single image analysis submitted.")

    # 4. Evidence Contradiction Check
    contradiction_found, contradiction_notes = detect_evidence_contradiction(disease_result)
    if contradiction_found:
        notes.extend(contradiction_notes)

    # 5. Calibrated Confidence Calculation
    has_ve = bool(disease_result.visual_evidence and disease_result.visual_evidence.directly_visible)
    calibrated_conf = calibrate_confidence(
        raw_confidence=disease_result.confidence,
        category=disease_result.category,
        image_quality_status=image_quality_status,
        crop_compatibility_status=crop_compatibility_status,
        contradiction_found=contradiction_found,
        has_visual_evidence=has_ve
    )
    disease_result.calibrated_confidence = calibrated_conf

    # 6. Evidence Level & Uncertainty Gate Decision
    if contradiction_found or crop_compatibility_status == "MISMATCHED_HOST":
        evidence_level = "LOW"
        is_uncertain = True
        notes.append("Evidence demoted to LOW due to structural evidence contradiction or host mismatch.")
    elif calibrated_conf >= 0.80 and image_quality_status in ("GOOD", "ACCEPTABLE") and crop_compatibility_status == "COMPATIBLE":
        evidence_level = "HIGH"
        is_uncertain = False
        notes.append(f"High evidence: calibrated confidence {calibrated_conf:.2f}, verified crop, and compatible symptoms.")
    elif calibrated_conf >= 0.60 and image_quality_status != "POOR":
        evidence_level = "MEDIUM"
        is_uncertain = False
        notes.append(f"Medium evidence: calibrated confidence {calibrated_conf:.2f}.")
    else:
        evidence_level = "LOW"
        is_uncertain = True
        notes.append(f"Low evidence: calibrated confidence {calibrated_conf:.2f} is below reliability threshold (0.60).")

    # 7. Targeted Close-Up Request Generation
    targeted_close_up_request = None
    if is_uncertain or image_quality_status in ("POOR", "SUBOPTIMAL") or contradiction_found:
        ve = disease_result.visual_evidence
        dom = ve.dominant_morphology if ve else "affected region"
        if contradiction_found or "cottony" in dom.lower() or "waxy" in dom.lower():
            targeted_close_up_request = (
                "Please capture a close-up macro photograph focusing directly on the white/cottony/waxy structures "
                "or leaf axils with bright, even lighting to distinguish between scale insects, mealybugs, and fungal growth."
            )
        elif image_quality_status == "SUBOPTIMAL":
            targeted_close_up_request = (
                "Image appears slightly blurry or distant. Please capture a clear, sharp close-up of the individual leaf lesion "
                "showing spot boundaries and surface texture."
            )
        else:
            targeted_close_up_request = (
                "Please provide a focused, close-up photograph of the symptom region with adequate lighting for precise diagnosis."
            )

    return DiagnosisValidationResult(
        evidence_level=evidence_level,
        image_quality_status=image_quality_status,
        crop_compatibility_status=crop_compatibility_status,
        consistency_status=consistency_status,
        is_uncertain=is_uncertain,
        calibrated_confidence=calibrated_conf,
        contradictory_evidence_found=contradiction_found,
        targeted_close_up_request=targeted_close_up_request,
        diagnosis_status="CONFIRMED" if not is_uncertain and calibrated_conf >= 0.80 else "UNCERTAIN",
        primary_diagnosis=disease_result.disease_name,
        primary_confidence=disease_result.confidence,
        gemini_verification="NOT_REQUIRED",
        validation_notes=notes
    )


def should_verify_with_gemini(
    primary_result: NormalizedDiseaseResult,
    primary_val: DiagnosisValidationResult,
    confidence_threshold: float = 0.80
) -> bool:
    """
    Determines whether Gemini second-opinion verification is required.
    Triggers ONLY IF:
      - Primary calibrated confidence < 0.80
      - OR evidence contradiction detected
      - OR image quality is SUBOPTIMAL or POOR
      - OR host mismatch / crop uncertain
      - OR category is UNKNOWN_UNCERTAIN
    """
    if primary_result.confidence is None:
        return True
    if primary_val.calibrated_confidence < confidence_threshold:
        return True
    if primary_val.contradictory_evidence_found:
        return True
    if primary_val.image_quality_status in ("POOR", "SUBOPTIMAL"):
        return True
    if primary_val.crop_compatibility_status != "COMPATIBLE":
        return True
    if primary_result.category in ("UNKNOWN_UNCERTAIN", "UNKNOWN"):
        return True

    return False


def reconcile_diagnoses(
    primary_result: NormalizedDiseaseResult,
    primary_val: DiagnosisValidationResult,
    gemini_result: Optional[NormalizedDiseaseResult]
) -> Tuple[NormalizedDiseaseResult, DiagnosisValidationResult]:
    """
    Reconciles primary provider diagnosis with independent Gemini second opinion:
    
    Case A (Agreement):
        Primary & Gemini match on disease name or category.
        -> status: CONFIRMED_BY_SECOND_OPINION, gemini_verification: AGREED
        
    Case B (Disagreement):
        Primary & Gemini conflict (e.g. Primary Fungal vs Gemini Pest).
        -> status: CONFLICTING, gemini_verification: DISAGREED, is_uncertain: True
        
    Case C (Gemini Uncertain):
        Gemini returns UNKNOWN / UNCERTAIN / confidence < 0.50.
        -> status: UNCERTAIN, gemini_verification: UNCERTAIN, is_uncertain: True
        
    Case D (Primary Low, Gemini High Support):
        Primary low confidence (e.g. 48%), Gemini high confidence (e.g. 86% same disease).
        -> status: CONFIRMED_BY_SECOND_OPINION, gemini_verification: AGREED
    """
    # If Gemini verification was not triggered (high confidence primary)
    if gemini_result is None and not primary_val.is_uncertain and primary_val.calibrated_confidence >= 0.80:
        primary_val.diagnosis_status = "CONFIRMED"
        primary_val.gemini_verification = "NOT_REQUIRED"
        primary_val.primary_diagnosis = primary_result.disease_name
        primary_val.primary_confidence = primary_result.confidence
        return primary_result, primary_val

    if gemini_result is None or gemini_result.category in ("UNKNOWN_UNCERTAIN", "UNKNOWN") or (gemini_result.confidence or 0.0) < 0.50:
        # Case C — Gemini Uncertain / Unavailable
        primary_val.diagnosis_status = "UNCERTAIN"
        primary_val.gemini_verification = "UNCERTAIN"
        primary_val.primary_diagnosis = primary_result.disease_name
        primary_val.primary_confidence = primary_result.confidence
        primary_val.is_uncertain = True
        primary_val.validation_notes.append("Gemini second-opinion analysis was uncertain or inconclusive.")
        return primary_result, primary_val

    p_name = (primary_result.disease_name or "").lower()
    g_name = (gemini_result.disease_name or "").lower()
    p_cat = (primary_result.category or "").upper()
    g_cat = (gemini_result.category or "").upper()

    # Check for direct or category agreement
    names_match = (p_name in g_name or g_name in p_name) and len(p_name) > 3
    categories_match = (p_cat == g_cat and p_cat not in ("UNKNOWN_UNCERTAIN", "UNKNOWN", ""))

    is_agreement = names_match or categories_match

    if is_agreement:
        # Case A / D — Agreement or Strong Gemini Confirmation
        final_disease = gemini_result if (gemini_result.confidence or 0) > (primary_result.confidence or 0) else primary_result
        primary_val.diagnosis_status = "CONFIRMED_BY_SECOND_OPINION"
        primary_val.gemini_verification = "AGREED"
        primary_val.primary_diagnosis = primary_result.disease_name
        primary_val.primary_confidence = primary_result.confidence
        primary_val.is_uncertain = False
        primary_val.calibrated_confidence = max(primary_val.calibrated_confidence, gemini_result.confidence or 0.80)
        primary_val.validation_notes.append(
            f"Diagnosis verified by independent AI second opinion ({gemini_result.disease_name})."
        )
        return final_disease, primary_val
    else:
        # Case B — Disagreement / Conflict
        primary_val.diagnosis_status = "CONFLICTING"
        primary_val.gemini_verification = "DISAGREED"
        primary_val.primary_diagnosis = primary_result.disease_name
        primary_val.primary_confidence = primary_result.confidence
        primary_val.is_uncertain = True
        primary_val.validation_notes.append(
            f"Diagnostic conflict: Primary provider suggests '{primary_result.disease_name}' ({primary_result.category}), "
            f"whereas independent visual analysis suggests '{gemini_result.disease_name}' ({gemini_result.category})."
        )
        return primary_result, primary_val

