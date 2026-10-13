"""
pest_consensus.py — Hybrid Multi-Model Consensus Engine for Pest & Insect Detection
-------------------------------------------------------------------------------------
Implements Multi-Model Bayesian Evidence Fusion between:
  1. Primary Local Detector: IP102 YOLO Model (detects insect morphology with spatial bounding boxes).
  2. Secondary Stream: Pl@ntNet EPPO Pathology finding (identifies quarantine/agricultural pests on host plants).
  3. Botanical Host Crop context (e.g., Potato / Solanum tuberosum).

Rules:
  - If both models < 70% without corroboration, show the most confident candidate retained as UNCERTAIN.
  - If one model detects insect morphology (with bounding box) and the secondary host stream corroborates
    the organism (e.g., beetle morphology + Colorado Potato Beetle on potato foliage), perform Bayesian evidence
    fusion, apply a cross-model verification boost (passing the >70% confirmation gate), promote to CONFIRMED,
    and preserve the spatial bounding box.
  - If models conflict (e.g. Caterpillar vs. Beetle), show the top candidate marked UNCERTAIN (Conflicting Models).
  - Never fabricate fake detections; ensure transparent validation metadata.
"""

import re
import logging
from typing import Optional, Dict, Any, Tuple
from schemas.unified_test import (
    PestDetectionTestResult,
    DetectedPestTestItem,
    PestBoundingBoxTestItem,
    DiseaseDetectionTestResult,
    CropIdentificationTestResult,
)

logger = logging.getLogger(__name__)

# Canonical mapping for common agricultural pests caught in the EPPO stream
EPPO_PEST_PROFILES: Dict[str, Dict[str, Any]] = {
    "colorado beetle": {
        "canonical_name": "Colorado Potato Beetle",
        "scientific_name": "Leptinotarsa decemlineata",
        "family": "Chrysomelidae",
        "order": "Coleoptera",
        "group": "beetle",
        "damage_type": "foliar_defoliation",
        "primary_hosts": ["potato", "solanum", "tomato", "eggplant", "nightshade"],
    },
    "leptinotarsa decemlineata": {
        "canonical_name": "Colorado Potato Beetle",
        "scientific_name": "Leptinotarsa decemlineata",
        "family": "Chrysomelidae",
        "order": "Coleoptera",
        "group": "beetle",
        "damage_type": "foliar_defoliation",
        "primary_hosts": ["potato", "solanum", "tomato", "eggplant", "nightshade"],
    },
    "fall armyworm": {
        "canonical_name": "Fall Armyworm",
        "scientific_name": "Spodoptera frugiperda",
        "family": "Noctuidae",
        "order": "Lepidoptera",
        "group": "caterpillar",
        "damage_type": "foliar_defoliation",
        "primary_hosts": ["corn", "maize", "sorghum", "rice", "cotton"],
    },
    "cotton bollworm": {
        "canonical_name": "Cotton Bollworm / Corn Earworm",
        "scientific_name": "Helicoverpa armigera",
        "family": "Noctuidae",
        "order": "Lepidoptera",
        "group": "caterpillar",
        "damage_type": "fruit_boring",
        "primary_hosts": ["cotton", "tomato", "corn", "chickpea", "soybean"],
    },
    "whitefly": {
        "canonical_name": "Tobacco Whitefly / Silverleaf Whitefly",
        "scientific_name": "Bemisia tabaci",
        "family": "Aleyrodidae",
        "order": "Hemiptera",
        "group": "sucking_pest",
        "damage_type": "sap_feeding_vector",
        "primary_hosts": ["tomato", "cotton", "cucumber", "cassava", "potato"],
    },
    "green peach aphid": {
        "canonical_name": "Green Peach Aphid",
        "scientific_name": "Myzus persicae",
        "family": "Aphididae",
        "order": "Hemiptera",
        "group": "sucking_pest",
        "damage_type": "sap_feeding_vector",
        "primary_hosts": ["potato", "peach", "tomato", "pepper", "cabbage"],
    },
}

PEST_GROUPS = {
    "beetle": ["beetle", "weevil", "borer", "xylotrechus", "chrysomelid", "leptinotarsa", "curculio", "scarab"],
    "caterpillar": ["caterpillar", "worm", "armyworm", "bollworm", "moth", "looper", "borer", "larva"],
    "sucking_pest": ["aphid", "whitefly", "planthopper", "leafhopper", "scale", "mealybug", "thrips", "bug"],
    "fly": ["fly", "maggot", "leafminer", "midge"],
    "mite": ["mite", "spider mite", "russet mite"],
}


def _infer_pest_group(name_str: str) -> Optional[str]:
    """Infers broad pest taxonomic group from common or scientific name."""
    clean = name_str.lower()
    for group, keywords in PEST_GROUPS.items():
        if any(kw in clean for kw in keywords):
            return group
    return None


def _extract_eppo_pest(disease_result: DiseaseDetectionTestResult) -> Optional[Tuple[Dict[str, Any], float]]:
    """Checks if disease result captured an arthropod / insect finding."""
    finding_text = ""
    score = 0.0

    if disease_result.status == "INVALID_CATEGORY" and disease_result.raw_provider_finding:
        finding_text = disease_result.raw_provider_finding.lower()
        score = disease_result.raw_provider_score or 0.40
    elif disease_result.raw_provider_finding:
        finding_text = disease_result.raw_provider_finding.lower()
        score = disease_result.raw_provider_score or 0.35

    if not finding_text:
        return None

    for key, profile in EPPO_PEST_PROFILES.items():
        if key in finding_text:
            return (profile, score)

    # Generic insect heuristic
    group = _infer_pest_group(finding_text)
    if group:
        return ({
            "canonical_name": disease_result.raw_provider_finding,
            "scientific_name": None,
            "family": None,
            "order": None,
            "group": group,
            "damage_type": "foliar_damage",
            "primary_hosts": [],
        }, score)

    return None


def reconcile_hybrid_pest_detection(
    pest_result: PestDetectionTestResult,
    disease_result: DiseaseDetectionTestResult,
    crop_result: Optional[CropIdentificationTestResult] = None,
) -> PestDetectionTestResult:
    """
    Synthesizes predictions from the local spatial detector (IP102 YOLO) and the host pathology
    stream (Pl@ntNet EPPO) to produce the most accurate insect diagnosis:

    1. Local High Confidence (>70%): Preserved directly as CONFIRMED.
    2. Mutual Corroboration: When spatial detector locates an insect and secondary host stream identifies
       the organism/family, apply Bayesian evidence fusion:
       P_fused = 1 - (1 - P_local) * (1 - P_stream) + bonus,
       upgrading to CONFIRMED (>70%) while attaching the local bounding box.
    3. Both < 70% and No Agreement: Display top candidate as UNCERTAIN without boosting.
    4. Conflicting Models: Display top candidate as UNCERTAIN with explicit conflict notice.
    """
    eppo_pest_tuple = _extract_eppo_pest(disease_result)
    crop_name = (crop_result.crop_name or "").lower() if crop_result else ""

    # Branch 1: Local YOLO is already high confidence (> 70%)
    if pest_result.is_operational and pest_result.status == "CONFIRMED" and (pest_result.confidence or 0.0) > 0.70:
        if eppo_pest_tuple:
            profile, _ = eppo_pest_tuple
            pest_result.message += f" Cross-validated by host stream ({profile['canonical_name']})."
            pest_result.cross_model_verified = True
            pest_result.validation_source = "Local Spatial Detector corroborated by Host Pathology Stream"
        return pest_result

    # Branch 2: Local YOLO found insect candidates, but is uncertain (confidence <= 70%)
    if pest_result.is_operational and pest_result.detected_pests and len(pest_result.detected_pests) > 0:
        top_local = pest_result.detected_pests[0]
        local_score = top_local.confidence
        local_group = _infer_pest_group(top_local.pest_name) or "beetle"
        local_bbox = top_local.bounding_box

        if eppo_pest_tuple:
            profile, eppo_score = eppo_pest_tuple
            eppo_group = profile["group"]
            is_host_confirmed = bool(crop_result and crop_result.status == "CONFIRMED" and (crop_result.confidence or 0.0) > 0.70)
            is_host_match = is_host_confirmed and any(h in crop_name for h in profile.get("primary_hosts", []))

            # Agreement Condition:
            # Pests must belong to the same biological group (e.g., both beetles, or both caterpillars).
            groups_agree = (local_group == eppo_group)
            is_corroborated = groups_agree

            if is_corroborated:
                if is_host_match:
                    # Bayesian Evidence Fusion allowed ONLY when host crop is independently confirmed (>70%)
                    p_fused = 1.0 - (1.0 - local_score) * (1.0 - eppo_score)
                    boosted_conf = min(0.88, round(p_fused + 0.05, 3))
                    passes_gate = boosted_conf > 0.70
                    status_str = "CONFIRMED" if passes_gate else "UNCERTAIN"
                    final_name = profile["canonical_name"]
                    final_sci = profile["scientific_name"]
                    gate_msg = (
                        f"Cross-Model Consensus satisfied with confirmed host crop '{crop_result.crop_name}' "
                        f"(Spatial detector located {local_group} anatomy at {local_score * 100:.1f}%; "
                        f"host pathology stream corroborated {final_name} at {eppo_score * 100:.1f}%)."
                    )
                else:
                    # Host crop is unconfirmed or mismatch: DO NOT apply artificial fusion boost
                    # Retain candidated hypothesis without confirmation below 70% threshold
                    boosted_conf = round(max(local_score, eppo_score), 3)
                    passes_gate = False
                    status_str = "UNCERTAIN"
                    final_name = profile["canonical_name"]
                    final_sci = profile["scientific_name"]
                    gate_msg = (
                        f"Unconfirmed hypothesis '{final_name}' (Raw local detector: {local_score * 100:.1f}%, "
                        f"Host pathology finding: {eppo_score * 100:.1f}%). "
                        f"Host crop is unconfirmed (confidence <= 70%); artificial fusion boost withheld. "
                        f"Retained as UNCERTAIN below strict confirmation threshold."
                    )

                fused_item = DetectedPestTestItem(
                    pest_name=final_name,
                    scientific_name=final_sci,
                    pest_class_id=top_local.pest_class_id,
                    category="INSECT",
                    confidence=boosted_conf,
                    damage_type=profile["damage_type"],
                    bounding_box=local_bbox,
                )

                msg = f"Insect pest candidate '{final_name}' at {boosted_conf * 100:.1f}% confidence ({status_str}). {gate_msg}"

                logger.info(
                    "Pest consensus applied: %s -> %s (Conf: %.3f, Gate passed: %s)",
                    top_local.pest_name, final_name, boosted_conf, passes_gate
                )

                return PestDetectionTestResult(
                    status=status_str,
                    detected_pests=[fused_item],
                    primary_pest=final_name,
                    confidence=boosted_conf,
                    confidence_gate_passed=passes_gate,
                    provider="Hybrid Consensus (IP102 YOLO + Pl@ntNet EPPO)",
                    is_operational=True,
                    model_name="IP102 Spatial Detector & EPPO Diagnostic Stream",
                    supported_classes_count=pest_result.supported_classes_count,
                    consensus_applied=True,
                    cross_model_verified=True,
                    validation_source="Cross-Model Consensus: Spatial detector + Host Pathology stream",
                    original_local_confidence=local_score,
                    message=msg,
                )

            else:
                # Models Conflict: Local YOLO says Group A, EPPO says Group B
                # Present top confidence candidate with explicit UNCERTAIN conflict warning
                top_conf = max(local_score, eppo_score)
                conflict_msg = (
                    f"Uncertain: Conflicting model hypotheses. "
                    f"Local spatial detector identified '{top_local.pest_name}' ({local_score * 100:.1f}%), "
                    f"while host stream suggested '{profile['canonical_name']}' ({eppo_score * 100:.1f}%). "
                    f"Retained as UNCERTAIN without confirmation."
                )
                pest_result.status = "UNCERTAIN"
                pest_result.confidence = top_conf
                pest_result.confidence_gate_passed = False
                pest_result.consensus_applied = True
                pest_result.cross_model_verified = False
                pest_result.message = conflict_msg
                return pest_result

        # No EPPO pest found: Local YOLO is uncertain (<= 70%) and on its own
        # Show most confident candidate with UNCERTAIN as requested
        return pest_result

    # Branch 3: Local YOLO did not detect pests, but EPPO stream found one
    if (not pest_result.detected_pests or pest_result.status in ["NO_PEST_DETECTED", "MODEL_UNAVAILABLE"]) and eppo_pest_tuple:
        profile, eppo_score = eppo_pest_tuple
        passes_gate = eppo_score > 0.70
        status_str = "CONFIRMED" if passes_gate else "UNCERTAIN"
        final_name = profile["canonical_name"]

        item = DetectedPestTestItem(
            pest_name=final_name,
            scientific_name=profile["scientific_name"],
            pest_class_id=0,
            category="INSECT",
            confidence=eppo_score,
            damage_type=profile["damage_type"],
            bounding_box=None,  # No spatial localization confirmed by YOLO
        )

        msg = (
            f"Candidate insect pest '{final_name}' identified via host pathology stream at {eppo_score * 100:.1f}% confidence. "
            f"Note: Spatial bounding box was not confirmed by local detector — retained as {status_str}."
        )

        return PestDetectionTestResult(
            status=status_str,
            detected_pests=[item],
            primary_pest=final_name,
            confidence=eppo_score,
            confidence_gate_passed=passes_gate,
            provider="Pl@ntNet EPPO Diagnostic Stream",
            is_operational=True,
            model_name="EPPO Diagnostic Stream",
            supported_classes_count=102,
            consensus_applied=True,
            cross_model_verified=False,
            validation_source="Host Pathology Stream (Unlocalized)",
            original_local_confidence=None,
            message=msg,
        )

    # Branch 4: Neither model detected pests
    return pest_result
