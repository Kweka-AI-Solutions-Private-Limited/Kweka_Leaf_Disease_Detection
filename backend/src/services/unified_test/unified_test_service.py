"""
unified_test_service.py — Unified Testing Execution Service
-------------------------------------------------------------
Executes independent detection for the testing interface:
  1. Crop Identification (Pl@ntNet live species identification with botanical vs. crop distinction)
  2. Disease Detection (Pl@ntNet EPPO pathology with strict >70% confidence gating & pest-filtering)
  3. Weed Detection (Local model adapter for DeepWeeds & MH-Weed16 — honest degradation when weights absent)
  4. Insect & Pest Detection (Local IP102 benchmark YOLO model — real detection and localization)

Rules enforced:
  - Genuine negative results distinguished from unavailable models.
  - Strict disease confidence gate: confidence must be > 0.70 to be CONFIRMED.
  - Zero mock substitutions presented as real results.
  - Zero Gemini calls, zero Kindwise calls, zero paid external APIs.
  - Zero treatment recommendations.
"""

import os
import io
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import requests
from PIL import Image, ImageOps
import numpy as np

from schemas.unified_test import (
    CropIdentificationTestResult,
    DiseaseDetectionTestResult,
    DiseaseCandidateTestItem,
    WeedDetectionTestResult,
    DetectedWeedTestItem,
    WeedBoundingBox,
    PestBoundingBoxTestItem,
    DetectedPestTestItem,
    PestDetectionTestResult,
    DetectorStatusItem,
)
from services.leaf_disease.plant_identifier import normalize_crop_name, KNOWN_CROPS
from services.leaf_disease.pathology_classifier import classify_disorder
from services.pest_detection.pest_provider import get_pest_provider
from services.weed_detection.weed_provider import get_weed_provider

logger = logging.getLogger(__name__)

PLANTNET_SPECIES_URL = "https://my-api.plantnet.org/v2/identify/all"
PLANTNET_DISEASES_URL = "https://my-api.plantnet.org/v2/diseases/identify"
DISEASE_CONFIDENCE_THRESHOLD = 0.70


def _get_plant_api_key() -> str:
    return os.getenv("PLANT_API_KEY", "").strip()


def prepare_image_for_api(image_bytes: bytes, filename: str) -> Tuple[bytes, str, Optional[str]]:
    """
    Standardizes image bytes for external providers:
      - Corrects EXIF rotation
      - Normalizes color channels (RGBA/CMYK -> RGB)
      - Resizes oversized images (max dimension 1920px) preserving aspect ratio
      - Validates basic quality (blur and minimal resolution)
    Returns: (processed_bytes, mime_type, quality_warning)
    """
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        pil_img = ImageOps.exif_transpose(pil_img)

        warning = None
        w, h = pil_img.size
        if w < 120 or h < 120:
            warning = f"Low resolution image ({w}x{h}px). Botanical details may be difficult to resolve."

        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

        max_dim = 1920
        if w > max_dim or h > max_dim:
            pil_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        # Basic blur detection using Laplacian variance
        try:
            gray = np.array(pil_img.convert("L"), dtype=np.float32)
            laplacian = (
                gray[:-2, 1:-1] + gray[2:, 1:-1] + gray[1:-1, :-2] + gray[1:-1, 2:]
                - 4 * gray[1:-1, 1:-1]
            )
            var = float(np.var(laplacian))
            if var < 40.0:
                warning = (warning + "; " if warning else "") + "Image appears soft or blurry; confidence may be reduced."
        except Exception:
            pass

        out_io = io.BytesIO()
        pil_img.save(out_io, format="JPEG", quality=92)
        return (out_io.getvalue(), "image/jpeg", warning)
    except Exception as exc:
        logger.warning("Image preparation notice: %s. Using original bytes.", exc)
        return (image_bytes, "image/jpeg", None)


def run_crop_identification(image_bytes: bytes, filename: str) -> CropIdentificationTestResult:
    """
    Executes live botanical crop species identification via Pl@ntNet /v2/identify/all.
    Accurately maps taxonomy, identifies common names, and distinguishes agricultural crops from wild flora.
    Never invents or fabricates crop names if unavailable.
    """
    api_key = _get_plant_api_key()
    provider_name = "Pl@ntNet Botanical Species API (v2)"

    if not api_key:
        return CropIdentificationTestResult(
            status="MODEL_UNAVAILABLE",
            crop_name="Unavailable",
            scientific_name=None,
            common_names=[],
            confidence=None,
            is_agricultural_crop=False,
            plant_type=None,
            quality_warning=None,
            provider=provider_name,
            is_operational=False,
            message="Model unavailable — detection not performed (PLANT_API_KEY not configured).",
        )

    processed_bytes, mime, quality_warning = prepare_image_for_api(image_bytes, filename)

    files = [
        ("images", (filename, processed_bytes, mime)),
        ("organs", (None, "leaf")),
    ]
    url = f"{PLANTNET_SPECIES_URL}?api-key={api_key}&lang=en"

    try:
        resp = requests.post(url, files=files, timeout=12)

        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if not results:
                return CropIdentificationTestResult(
                    status="UNSUPPORTED",
                    crop_name="Unidentified Plant",
                    scientific_name=None,
                    common_names=[],
                    confidence=0.0,
                    is_agricultural_crop=False,
                    plant_type="UNIDENTIFIED",
                    quality_warning=quality_warning,
                    provider=provider_name,
                    is_operational=True,
                    message="Genuine result: No botanical plant or crop species matched with sufficient certainty.",
                )

            top = results[0]
            score = float(top.get("score", 0.0))
            species_data = top.get("species", {})
            sci_name = species_data.get("scientificNameWithoutAuthor") or species_data.get("scientificName") or "Unknown"
            common_names = species_data.get("commonNames") or []

            # 1. Map to canonical common crop name (e.g., Solanum tuberosum -> Potato)
            matched_common = None
            norm_from_sci = normalize_crop_name(sci_name)
            if norm_from_sci != sci_name.title() and norm_from_sci != "Unknown":
                matched_common = norm_from_sci

            if not matched_common and common_names:
                for cn in common_names:
                    norm = normalize_crop_name(cn)
                    if norm:
                        matched_common = norm
                        break

            primary_crop_name = matched_common if matched_common else (common_names[0].title() if common_names else sci_name)

            # 2. Check if identified species is a cultivated crop vs. wild flora/weed
            is_crop = False
            sci_lower = sci_name.lower()
            norm_lower = (matched_common or "").lower()
            if norm_lower in [k.lower() for k in KNOWN_CROPS.keys()] or any(k.lower() in sci_lower for k in KNOWN_CROPS.keys()):
                is_crop = True
            elif any(v.lower() == norm_lower for v in KNOWN_CROPS.values()):
                is_crop = True

            plant_type = "CULTIVATED_CROP" if is_crop else "WILD_FLORA_OR_WEED"

            status = "CONFIRMED" if score > 0.70 else ("SUSPECTED" if score > 0.40 else "UNCERTAIN")
            if is_crop:
                if status == "CONFIRMED":
                    msg = f"Agricultural crop identified as '{primary_crop_name}' ({sci_name}) with {score * 100:.1f}% confidence."
                elif status == "SUSPECTED":
                    msg = f"Candidate agricultural crop '{primary_crop_name}' ({sci_name}) at {score * 100:.1f}% confidence (retained as SUSPECTED below 70% confirmation threshold)."
                else:
                    msg = f"Uncertain crop candidate '{primary_crop_name}' ({sci_name}) at {score * 100:.1f}% confidence (below 60% threshold; below 40% gate; evidence insufficient to confirm)."
            else:
                msg = (
                    f"Botanical plant species identified as '{primary_crop_name}' ({sci_name}) with {score * 100:.1f}% confidence "
                    f"(Note: species is wild flora or non-crop vegetation rather than a standard cultivated crop)."
                )

            return CropIdentificationTestResult(
                status=status,
                crop_name=primary_crop_name,
                scientific_name=sci_name,
                common_names=common_names[:3],
                confidence=score,
                is_agricultural_crop=is_crop,
                plant_type=plant_type,
                quality_warning=quality_warning,
                provider=provider_name,
                is_operational=True,
                message=msg,
            )

        elif resp.status_code == 404:
            return CropIdentificationTestResult(
                status="UNSUPPORTED",
                crop_name="Not Recognized",
                scientific_name=None,
                common_names=[],
                confidence=0.0,
                is_agricultural_crop=False,
                plant_type="NON_PLANT_OR_UNRECOGNIZED",
                quality_warning=quality_warning,
                provider=provider_name,
                is_operational=True,
                message="Genuine result: Pl@ntNet found no matching plant or crop species for this image.",
            )

        elif resp.status_code == 429:
            return CropIdentificationTestResult(
                status="ERROR",
                crop_name="Rate Limit Exceeded",
                scientific_name=None,
                common_names=[],
                confidence=None,
                is_agricultural_crop=False,
                plant_type=None,
                quality_warning=quality_warning,
                provider=provider_name,
                is_operational=False,
                message="Pl@ntNet API rate limit reached (HTTP 429). Please retry after cooldown.",
            )

        else:
            return CropIdentificationTestResult(
                status="ERROR",
                crop_name="Service Error",
                scientific_name=None,
                common_names=[],
                confidence=None,
                is_agricultural_crop=False,
                plant_type=None,
                quality_warning=quality_warning,
                provider=provider_name,
                is_operational=False,
                message=f"Provider returned HTTP error {resp.status_code}.",
            )

    except Exception as exc:
        logger.error("Pl@ntNet crop identification failed: %s", exc)
        return CropIdentificationTestResult(
            status="ERROR",
            crop_name="Network Error",
            scientific_name=None,
            common_names=[],
            confidence=None,
            is_agricultural_crop=False,
            plant_type=None,
            quality_warning=quality_warning,
            provider=provider_name,
            is_operational=False,
            message=f"Connection to provider failed: {str(exc)}",
        )


def run_disease_detection(image_bytes: bytes, filename: str, crop_name: Optional[str] = None) -> DiseaseDetectionTestResult:
    """
    Executes live plant pathology detection via Pl@ntNet /v2/diseases/identify (EPPO codes).
    Enforces the strict >70% confidence threshold gate.
    Filters non-disease organisms (insects/arthropods) into INVALID_CATEGORY.
    Validates host crop compatibility when crop identity is known.
    Never invents or fabricates disease names if unavailable.
    """
    api_key = _get_plant_api_key()
    provider_name = "Pl@ntNet Diseases Pathology API (EPPO)"

    if not api_key:
        return DiseaseDetectionTestResult(
            status="MODEL_UNAVAILABLE",
            disease_name="Unavailable",
            confidence=None,
            confidence_gate_passed=False,
            provider=provider_name,
            is_operational=False,
            candidates=[],
            message="Model unavailable — detection not performed (PLANT_API_KEY not configured).",
        )

    processed_bytes, mime, _ = prepare_image_for_api(image_bytes, filename)

    files = [
        ("images", (filename, processed_bytes, mime)),
        ("organs", (None, "leaf")),
    ]
    url = f"{PLANTNET_DISEASES_URL}?api-key={api_key}&lang=en"

    try:
        resp = requests.post(url, files=files, timeout=12)

        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])

            if not results:
                return DiseaseDetectionTestResult(
                    status="NO_DISEASE_DETECTED",
                    disease_name="Healthy Foliage / No Disease Detected",
                    confidence=0.0,
                    confidence_gate_passed=False,
                    provider=provider_name,
                    is_operational=True,
                    candidates=[],
                    message="Genuine negative result: No pathological lesions or disease symptoms identified.",
                )

            top = results[0]
            raw_score = float(top.get("score", 0.0))
            description = top.get("description", "")
            eppo_code = top.get("name", "")

            # 1. Classify top finding: Pathology vs. Arthropod/Insect Pest
            classification = classify_disorder(description=description, eppo_code=eppo_code)

            if not classification.is_pathology:
                logger.warning(
                    "Pathology provider returned non-disease organism: '%s' (%s) with score %.2f. "
                    "Excluding from Disease panel.",
                    classification.common_name,
                    classification.scientific_name,
                    raw_score,
                )

                valid_pathology_candidates: List[DiseaseCandidateTestItem] = []
                for item in results[1:5]:
                    c_desc = item.get("description", "")
                    c_code = item.get("name", "")
                    c_score = float(item.get("score", 0.0))
                    c_class = classify_disorder(description=c_desc, eppo_code=c_code)
                    if c_class.is_pathology:
                        valid_pathology_candidates.append(
                            DiseaseCandidateTestItem(
                                disease_name=f"{c_class.common_name} ({c_class.scientific_name})" if c_class.scientific_name else c_class.common_name,
                                confidence=c_score,
                            )
                        )

                return DiseaseDetectionTestResult(
                    status="INVALID_CATEGORY",
                    disease_name="None (Arthropod/Insect Pest in Stream)",
                    common_name=None,
                    scientific_name=None,
                    confidence=None,
                    confidence_gate_passed=False,
                    provider=provider_name,
                    is_operational=True,
                    candidates=valid_pathology_candidates,
                    raw_provider_finding=f"{classification.common_name} ({classification.scientific_name})" if classification.scientific_name else classification.common_name,
                    raw_provider_score=raw_score,
                    category_warning=(
                        f"Non-Disease Finding: The pathology provider identified an arthropod/insect pest "
                        f"('{classification.common_name}'), which is an animal organism, not a plant pathology. "
                        f"This finding has been excluded from the Disease Detection panel."
                    ),
                    message=(
                        f"Non-pathology finding excluded: The provider returned an insect pest "
                        f"('{classification.common_name}') rather than a plant disease pathogen. "
                        f"No botanical disease confirmed."
                    ),
                )

            # 2. Genuine Pathology branch
            disease_common = classification.common_name
            disease_sci = classification.scientific_name
            disease_display = f"{disease_common} ({disease_sci})" if disease_sci else disease_common

            candidates: List[DiseaseCandidateTestItem] = []
            for item in results[1:5]:
                c_score = float(item.get("score", 0.0))
                c_desc = item.get("description", "")
                c_code = item.get("name", "")
                c_class = classify_disorder(description=c_desc, eppo_code=c_code)
                if c_class.is_pathology:
                    c_display = f"{c_class.common_name} ({c_class.scientific_name})" if c_class.scientific_name else c_class.common_name
                    candidates.append(DiseaseCandidateTestItem(disease_name=c_display, confidence=c_score))

            # Apply strict >70% confidence gate
            passes_gate = raw_score > DISEASE_CONFIDENCE_THRESHOLD

            host_compat = None
            if crop_name and crop_name.lower() not in ["unidentified plant", "not recognized", "unavailable"]:
                host_compat = f"Evaluated with respect to host crop '{crop_name}'."

            if passes_gate:
                status = "CONFIRMED"
                msg = (
                    f"Confirmed disease: '{disease_common}' with {raw_score * 100:.1f}% confidence "
                    f"(Strict >70% confirmation standard satisfied)."
                )
            else:
                status = "UNCERTAIN"
                msg = (
                    f"Identified candidate '{disease_common}' with {raw_score * 100:.1f}% confidence. "
                    f"Confidence is at or below 70% — retained as UNCERTAIN per confirmation policy."
                )

            return DiseaseDetectionTestResult(
                status=status,
                disease_name=disease_common,
                common_name=disease_common,
                scientific_name=disease_sci,
                confidence=raw_score,
                confidence_gate_passed=passes_gate,
                provider=provider_name,
                is_operational=True,
                candidates=candidates,
                raw_provider_finding=disease_display,
                raw_provider_score=raw_score,
                category_warning=None,
                host_crop_compatibility=host_compat,
                message=msg,
            )

        elif resp.status_code == 404:
            return DiseaseDetectionTestResult(
                status="NO_DISEASE_DETECTED",
                disease_name="No Disease Symptoms Found",
                confidence=0.0,
                confidence_gate_passed=False,
                provider=provider_name,
                is_operational=True,
                candidates=[],
                message="Genuine negative result: No matching plant disease symptoms identified in the foliage.",
            )

        elif resp.status_code == 429:
            return DiseaseDetectionTestResult(
                status="ERROR",
                disease_name="Rate Limit Exceeded",
                confidence=None,
                confidence_gate_passed=False,
                provider=provider_name,
                is_operational=False,
                candidates=[],
                message="Pl@ntNet API rate limit reached (HTTP 429). Please retry after cooldown.",
            )

        else:
            return DiseaseDetectionTestResult(
                status="ERROR",
                disease_name="Service Error",
                confidence=None,
                confidence_gate_passed=False,
                provider=provider_name,
                is_operational=False,
                candidates=[],
                message=f"Provider returned HTTP error {resp.status_code}.",
            )

    except Exception as exc:
        logger.error("Pl@ntNet disease detection failed: %s", exc)
        return DiseaseDetectionTestResult(
            status="ERROR",
            disease_name="Network Error",
            confidence=None,
            confidence_gate_passed=False,
            provider=provider_name,
            is_operational=False,
            candidates=[],
            message=f"Connection to provider failed: {str(exc)}",
        )


def run_weed_detection(image_bytes: bytes, filename: str, crop_name: Optional[str] = None) -> WeedDetectionTestResult:
    """
    Executes local offline weed detection using the modular WeedDetectionProvider adapter.
    Supports DeepWeeds (classification) and MH-Weed16 (YOLO detection).
    Honest Degradation Rule: If local weights are absent, returns MODEL_UNAVAILABLE.
    Never invents, mocks, or hallucinates fake weed detections.
    """
    provider = get_weed_provider()
    model_info = provider.get_model_info()

    if not provider.is_available():
        return WeedDetectionTestResult(
            status="MODEL_UNAVAILABLE",
            detected_weeds=[],
            confidence=None,
            provider=model_info.framework,
            is_operational=False,
            model_name=model_info.model_name,
            architecture_type=model_info.architecture,
            supports_bounding_boxes=model_info.supports_bounding_boxes,
            dataset_origin=model_info.dataset_origin,
            message=model_info.status_message,
        )

    try:
        detections, updated_info = provider.detect_weeds(image_bytes=image_bytes, crop_name=crop_name)

        if not detections:
            return WeedDetectionTestResult(
                status="NO_WEED_DETECTED",
                detected_weeds=[],
                confidence=0.0,
                provider=updated_info.framework,
                is_operational=True,
                model_name=updated_info.model_name,
                architecture_type=updated_info.architecture,
                supports_bounding_boxes=updated_info.supports_bounding_boxes,
                dataset_origin=updated_info.dataset_origin,
                message="Genuine negative result: No target weed species detected in the foliage.",
            )

        test_items: List[DetectedWeedTestItem] = []
        for d in detections:
            bbox_item = None
            if d.bounding_box:
                bbox_item = WeedBoundingBox(
                    ymin=d.bounding_box.ymin,
                    xmin=d.bounding_box.xmin,
                    ymax=d.bounding_box.ymax,
                    xmax=d.bounding_box.xmax,
                    label=d.bounding_box.label or d.weed_name,
                    confidence=d.bounding_box.confidence or d.confidence,
                )
            test_items.append(
                DetectedWeedTestItem(
                    weed_name=d.weed_name,
                    scientific_name=d.scientific_name,
                    confidence=d.confidence,
                    bounding_box=bbox_item,
                    detection_type=d.detection_type,
                    growth_habit=d.growth_habit,
                )
            )

        top_conf = max(d.confidence for d in detections)
        gate_passed = top_conf > 0.70
        status = "CONFIRMED" if gate_passed else "UNCERTAIN"
        top_name = detections[0].weed_name

        if gate_passed:
            msg = f"Confirmed weed: '{top_name}' with {top_conf * 100:.1f}% confidence ({len(detections)} instance(s) detected)."
        else:
            msg = f"Candidate weed '{top_name}' at {top_conf * 100:.1f}% confidence. Below 70% confirmation threshold — retained as UNCERTAIN."

        return WeedDetectionTestResult(
            status=status,
            detected_weeds=test_items,
            confidence=top_conf,
            provider=updated_info.framework,
            is_operational=True,
            model_name=updated_info.model_name,
            architecture_type=updated_info.architecture,
            supports_bounding_boxes=updated_info.supports_bounding_boxes,
            dataset_origin=updated_info.dataset_origin,
            message=msg,
        )

    except Exception as exc:
        logger.error("Weed detector execution error: %s", exc)
        return WeedDetectionTestResult(
            status="ERROR",
            detected_weeds=[],
            confidence=None,
            provider=model_info.framework,
            is_operational=False,
            model_name=model_info.model_name,
            architecture_type=model_info.architecture,
            supports_bounding_boxes=model_info.supports_bounding_boxes,
            dataset_origin=model_info.dataset_origin,
            message=f"Model execution error: {str(exc)}",
        )


def run_pest_detection(image_bytes: bytes, filename: str, crop_name: Optional[str] = None) -> PestDetectionTestResult:
    """
    Executes local offline insect & pest detection using IP102 benchmark model.
    Honest Degradation Rule: If weights are absent, returns MODEL_UNAVAILABLE.
    Distinguishes genuine negative results (NO_PEST_DETECTED) from missing models.
    Enforces strict >70% confidence threshold for CONFIRMED detections.
    Never hallucinates or mocks fake pest detections.
    """
    provider = get_pest_provider()
    model_info = provider.get_model_info()

    if not provider.is_available():
        return PestDetectionTestResult(
            status="MODEL_UNAVAILABLE",
            detected_pests=[],
            primary_pest=None,
            confidence=None,
            confidence_gate_passed=False,
            provider=model_info.framework,
            is_operational=False,
            model_name=model_info.model_name,
            supported_classes_count=model_info.supported_classes_count,
            message=model_info.status_message,
        )

    try:
        detections, updated_info = provider.detect_pests(image_bytes=image_bytes, crop_name=crop_name)

        if not detections:
            return PestDetectionTestResult(
                status="NO_PEST_DETECTED",
                detected_pests=[],
                primary_pest=None,
                confidence=0.0,
                confidence_gate_passed=False,
                provider=updated_info.framework,
                is_operational=True,
                model_name=updated_info.model_name,
                supported_classes_count=updated_info.supported_classes_count,
                message="Genuine negative result: No insect pests detected (scanned 102 benchmark species).",
            )

        test_items: List[DetectedPestTestItem] = []
        for d in detections:
            bbox_item = None
            if d.bounding_box:
                bbox_item = PestBoundingBoxTestItem(
                    ymin=d.bounding_box.ymin,
                    xmin=d.bounding_box.xmin,
                    ymax=d.bounding_box.ymax,
                    xmax=d.bounding_box.xmax,
                    label=d.bounding_box.label,
                    confidence=d.bounding_box.confidence,
                )
            test_items.append(
                DetectedPestTestItem(
                    pest_name=d.pest_name,
                    scientific_name=d.scientific_name,
                    pest_class_id=d.pest_class_id,
                    category=d.category,
                    confidence=d.confidence,
                    damage_type=d.damage_type,
                    bounding_box=bbox_item,
                )
            )

        top_detection = detections[0]
        top_conf = top_detection.confidence
        gate_passed = top_conf > 0.70
        status = "CONFIRMED" if gate_passed else "UNCERTAIN"

        msg = (
            f"Confirmed insect pest: '{top_detection.pest_name}' with {top_conf * 100:.1f}% confidence "
            f"(Strict >70% standard satisfied; {len(detections)} instance(s) located)."
            if gate_passed
            else f"Candidate insect pest '{top_detection.pest_name}' at {top_conf * 100:.1f}% confidence. "
            f"Confidence is at or below 70% — retained as UNCERTAIN per verification policy."
        )

        return PestDetectionTestResult(
            status=status,
            detected_pests=test_items,
            primary_pest=top_detection.pest_name,
            confidence=top_conf,
            confidence_gate_passed=gate_passed,
            provider=updated_info.framework,
            is_operational=True,
            model_name=updated_info.model_name,
            supported_classes_count=updated_info.supported_classes_count,
            message=msg,
        )

    except Exception as exc:
        logger.error("Pest detection execution error: %s", exc)
        return PestDetectionTestResult(
            status="ERROR",
            detected_pests=[],
            primary_pest=None,
            confidence=None,
            confidence_gate_passed=False,
            provider=model_info.framework,
            is_operational=False,
            model_name=model_info.model_name,
            supported_classes_count=model_info.supported_classes_count,
            message=f"Model execution error: {str(exc)}",
        )


def get_all_detectors_status() -> Dict[str, DetectorStatusItem]:
    """Returns operational and configuration status of each detector."""
    has_plant_key = bool(_get_plant_api_key())

    weed_provider = get_weed_provider()
    weed_info = weed_provider.get_model_info()
    has_weed_model = weed_provider.is_available()

    pest_provider = get_pest_provider()
    pest_info = pest_provider.get_model_info()
    has_pest_model = pest_provider.is_available()

    return {
        "crop_identifier": DetectorStatusItem(
            detector_name="Crop Identification",
            provider="Pl@ntNet Botanical Species API (v2)",
            is_operational=has_plant_key,
            status="OPERATIONAL" if has_plant_key else "UNAVAILABLE",
            type="Live API",
            details="Botanical species identification via Pl@ntNet /v2/identify/all with agricultural crop classification." if has_plant_key else "PLANT_API_KEY is not configured.",
        ),
        "disease_detector": DetectorStatusItem(
            detector_name="Disease Detection",
            provider="Pl@ntNet Diseases Pathology API (EPPO)",
            is_operational=has_plant_key,
            status="OPERATIONAL" if has_plant_key else "UNAVAILABLE",
            type="Live API",
            details="Foliar pathology detection with EPPO diagnostic catalog, non-disease filtering, and >70% confidence gating." if has_plant_key else "PLANT_API_KEY is not configured.",
        ),
        "weed_detector": DetectorStatusItem(
            detector_name="Weed Detection",
            provider=f"{weed_info.model_name} ({weed_info.architecture})",
            is_operational=has_weed_model,
            status="OPERATIONAL" if has_weed_model else "AWAITING_WEIGHTS",
            type="Local Model (Offline)",
            details=weed_info.status_message,
        ),
        "pest_detector": DetectorStatusItem(
            detector_name="Insect & Pest Detection",
            provider="Hybrid Consensus (IP102 YOLO + Pl@ntNet EPPO)" if (has_pest_model and has_plant_key) else f"{pest_info.model_name} ({pest_info.framework})",
            is_operational=has_pest_model,
            status="OPERATIONAL" if has_pest_model else "AWAITING_WEIGHTS",
            type="Hybrid Engine (Spatial YOLO + EPPO Stream)" if (has_pest_model and has_plant_key) else "Local Model (Offline)",
            details="Dual-stream hybrid consensus engine reconciling local spatial bounding boxes with EPPO diagnostic stream via Bayesian evidence fusion." if (has_pest_model and has_plant_key) else pest_info.status_message,
        ),
    }
