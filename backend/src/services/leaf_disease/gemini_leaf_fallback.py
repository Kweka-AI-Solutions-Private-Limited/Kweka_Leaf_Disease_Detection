"""
gemini_leaf_fallback.py — Gemini Vision Fallback for Leaf Disease Pipeline (Phase 1+)
---------------------------------------------------------------------------------------
Provides targeted Gemini VLM calls when primary providers fail or return low-confidence:
  - Crop identification fallback: When auto-detect returns UNCERTAIN/Unknown
  - Disease enrichment fallback: When primary disease provider returns LOW evidence

STRICT RULES:
  - Never used as primary provider. Always secondary/fallback only.
  - Returns structured, normalized results matching existing schemas.
  - Zero NACL product matching, zero treatment recommendations.
  - Never logs or exposes the API key.
"""

import os
import json
import logging
from typing import List, Optional, Tuple, Any, Dict

from schemas.leaf_disease import CropIdentificationResult, NormalizedDiseaseResult, DiseaseCandidate, ImageValidationDetail

logger = logging.getLogger(__name__)

CROP_IDENTIFY_PROMPT = """You are an expert agricultural botanist and plant taxonomist specializing in precision crop identification for digital plant pathology.

You are given one or more leaf/plant photographs. Identify the exact crop or plant species based on strict morphological features.

Botanical Identification Guidelines:
- Anacardiaceae (Mango): Long, lanceolate, leathery leaves with prominent midrib and wavy/entire margins; pinkish young leaves maturing to dark shiny green.
- Myrtaceae (Guava): Opposite, oblong/elliptic leathery leaves with prominent parallel secondary veins depressed on upper surface.
- Solanaceae (Tomato, Potato, Pepper, Eggplant): Compound pinnate leaves (Tomato/Potato) or simple ovate leaves (Pepper/Eggplant) with glandular hairs.
- Cucurbitaceae (Cucumber, Melon, Squash, Pumpkin): Broad palmate/cordate leaves with 3-5 shallow lobes, coarse texture, hairy trailing vines.
- Poaceae (Rice / Paddy, Wheat, Maize / Corn, Sugarcane): Linear blade leaves with parallel venation and ligule/sheath at stem node.
- Malvaceae (Cotton): 3 to 5-lobed palmate leaves with extrafloral nectaries on leaf veins.
- Fabaceae (Soybean, Groundnut / Peanut, Pulses): Trifoliate or pinnately compound leaves with pulvinus base.
- Rutaceae (Citrus / Lemon / Orange): Winged petiole, dark glossy oval leaves with translucent oil glands.
- Vitaceae (Grape): Deeply palmately lobed leaves with coarse serrated edges and climbing tendrils.
- Rosaceae (Apple, Pear): Oval leaves with fine serrations on woody shoots.
- Musaceae (Banana): Massive broad paddle-like leaf blades with parallel transverse venation.

Instructions:
1. Carefully examine blade morphology, leaf arrangement, venation pattern, margin serrations, and stem/petiole structure.
2. Select the most accurate crop name from: Mango, Guava, Tomato, Potato, Chilli / Pepper, Cucurbits, Brinjal / Eggplant, Rice / Paddy, Wheat, Maize / Corn, Sugarcane, Cotton, Groundnut / Peanut, Soybean, Citrus, Grape, Apple, Pear, Banana, Papaya, Pomegranate, Onion, Garlic, Okra / Bhindi, Cabbage, Tea, Coffee.
3. If confident, return the exact crop name. If visual features are ambiguous or insufficient, return "Unknown".
4. Do NOT guess a crop based on disease symptoms. Crop identification must rely strictly on leaf morphology.

Return ONLY valid JSON format — no markdown, no explanation wrapper:
{
  "crop_name": "<common crop name>",
  "confidence": <float 0.0-1.0>,
  "evidence_note": "<1-2 sentences detailing specific botanical morphology features observed>"
}"""

DISEASE_ANALYSIS_PROMPT = """You are an expert agricultural plant pathologist and visual diagnostician. Conduct a rigorous visual analysis of the provided leaf image(s) to diagnose plant health, disease symptoms, or pest damage.

CRITICAL MULTI-STEP DIAGNOSTIC PROTOCOL:

1. HEALTHY LEAF CHECK:
   - If the leaf shows uniform green coloration, intact tissue, and zero signs of lesions, pustules, wilting, or pest damage -> Classify as "Healthy / No Disease Detected" with category "HEALTHY".

2. VISUAL EVIDENCE OBSERVATION (Examine ALL visible images as a multi-angle diagnostic sample):
   - Lesion Morphology: Circular, irregular, angular (vein-bounded), target-ring concentric circles, halo rings, shot-hole perforations.
   - Lesion Color & Stage: Yellow chlorotic spots, dark brown/black necrotic centers, rust-orange pustules, translucent water-soaked spots.
   - Pathogen Structures:
     * Flour-like white powder on upper leaf surface -> POWDERY MILDEW FUNGUS
     * Downy/purple fungal growth on leaf underside -> DOWNY MILDEW FUNGUS
     * Dark pinhead specks (pycnidia) inside necrotic spots -> SEPTORIA / ALTERNARIA FUNGAL BLIGHT
     * White, cottony, waxy masses or scale covers at leaf axils/stems -> PEST / MEALYBUG / SCALE INSECT
     * Feeding punctures, webbing, leaf curling, or mosaic mottling -> INSECT / SPIDER MITE / VIRAL INFECTION

3. DIAGNOSTIC CATEGORY SELECTION:
   - "HEALTHY": Normal green leaf, zero lesions or pest damage.
   - "FUNGAL": Distinct fungal lesions, concentric rings, fruiting bodies, powdery dusting, or rust pustules dominate.
   - "BACTERIAL": Water-soaked angular lesions with yellow halos, leaf streaks, or ooze dominate.
   - "VIRAL": Mosaic patterns, vein clearing, severe leaf curling, or systemic mottling dominate.
   - "PEST_INSECT": Cottony/waxy masses, scale insect covers, visible insects, webbing, or direct feeding holes dominate.
   - "NUTRIENT_PHYSIOLOGICAL": Interveinal chlorosis, marginal tip burn, or sunscorch dominate without pathogen structures.
   - "UNKNOWN_UNCERTAIN": Image is blurry, out-of-focus, dark, distant, or contradictory.

4. CANDIDATE DIAGNOSES & CONFIDENCE:
   - Provide the primary diagnosis formatted as: "Common Name (Scientific Name)" e.g., "Early Blight (Alternaria solani)" or "Anthracnose (Colletotrichum gloeosporioides)".
   - Include up to 4 differential candidate diagnoses with category, confidence (0.0 to 1.0), and visual evidence match score.
   - Estimate affected leaf surface coverage percentage (0% to 100%) and severity level (NONE | LOW | MODERATE | SEVERE).

Return ONLY valid JSON matching this exact structure — no markdown wrapper:
{
  "category": "HEALTHY | FUNGAL | BACTERIAL | VIRAL | PEST_INSECT | NUTRIENT_PHYSIOLOGICAL | UNKNOWN_UNCERTAIN",
  "disease_name": "<Common Name (Scientific Name) or Condition>",
  "confidence": <float 0.0-1.0>,
  "is_healthy": <true/false>,
  "visual_evidence": {
    "directly_visible": ["list of observed features (colors, shapes, textures, structures)"],
    "inferred": ["inferred diagnostic context"],
    "unavailable": ["missing evidence needed for exact sub-species confirmation"],
    "dominant_morphology": "description of dominant visual structure"
  },
  "candidates": [
    {
      "name": "<Condition Name>",
      "category": "<HEALTHY | FUNGAL | BACTERIAL | VIRAL | PEST_INSECT | NUTRIENT_PHYSIOLOGICAL | UNKNOWN_UNCERTAIN>",
      "confidence": <float 0.0-1.0>,
      "evidence_match_score": <float 0.0-1.0>
    }
  ],
  "evidence_note": "<1-2 sentences explaining visual evidence leading to this category>",
  "close_up_request": "<Targeted request for additional visual evidence if image is ambiguous, or null if clear>"
}"""


def _get_gemini_client():
    """Returns configured Gemini client using existing project API key."""
    try:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            return None, None
        model_name = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
        client = genai.Client(api_key=api_key)
        return client, model_name
    except ImportError:
        logger.error("google-genai package not installed.")
        return None, None


def gemini_identify_crop(
    raw_files: List[Tuple[str, bytes]]
) -> Optional[CropIdentificationResult]:
    """
    Calls Gemini Vision to identify crop from leaf images.
    Called ONLY when primary auto-detection returns UNCERTAIN.
    Returns CropIdentificationResult or None if Gemini is unavailable/fails.
    """
    client, model_name = _get_gemini_client()
    if not client:
        logger.warning("Gemini crop identification fallback skipped: GEMINI_API_KEY not configured.")
        return None

    try:
        from google.genai import types
        import io

        contents: List[Any] = [CROP_IDENTIFY_PROMPT]
        for filename, img_bytes in raw_files[:3]:  # Max 3 images to Gemini
            mime = "image/jpeg"
            if filename.lower().endswith(".png"):
                mime = "image/png"
            elif filename.lower().endswith(".webp"):
                mime = "image/webp"
            part = types.Part.from_bytes(data=img_bytes, mime_type=mime)
            contents.append(part)

        if len(contents) < 2:
            return None

        logger.info("Calling Gemini crop identification fallback with %d images.", len(raw_files))
        
        # Try candidate models in order of stability
        candidate_models = [model_name or "gemini-flash-latest", "gemini-flash-latest", "gemini-2.0-flash", "gemini-1.5-flash"]
        response = None
        for m in candidate_models:
            try:
                response = client.models.generate_content(
                    model=m,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                if response and response.text:
                    break
            except Exception as ex:
                logger.debug("Model %s failed for crop identify: %s", m, ex)
                continue

        if not response or not response.text:
            return None

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        parsed = json.loads(raw_text)

        crop_name = parsed.get("crop_name", "Unknown").strip()
        confidence = float(parsed.get("confidence", 0.0))
        evidence_note = parsed.get("evidence_note", "Identified by Gemini Vision VLM.")

        if not crop_name or crop_name.lower() == "unknown":
            return CropIdentificationResult(
                crop_name="Unknown",
                confidence=0.0,
                source="gemini_fallback",
                status="UNCERTAIN",
                evidence_note="Gemini Vision could not identify the crop with confidence."
            )

        return CropIdentificationResult(
            crop_name=crop_name,
            confidence=confidence,
            source="gemini_fallback",
            status="CONFIRMED" if confidence >= 0.60 else "UNCERTAIN",
            evidence_note=f"[Gemini Vision] {evidence_note}"
        )

    except Exception as e:
        logger.error("Gemini crop identification fallback failed: %s", str(e))
        return None


def gemini_analyze_disease(
    crop_name: str,
    raw_files: List[Tuple[str, bytes]]
) -> Optional[NormalizedDiseaseResult]:
    """
    Calls Gemini Vision for evidence-first disease/pest analysis.
    Executes structured visual observations prior to candidate classification.
    """
    client, model_name = _get_gemini_client()
    if not client:
        logger.warning("Gemini disease fallback skipped: GEMINI_API_KEY not configured.")
        return None

    try:
        from google.genai import types
        from schemas.leaf_disease import VisualEvidenceDetail

        prompt = DISEASE_ANALYSIS_PROMPT
        if crop_name and crop_name.lower() != "unknown":
            prompt = f"Crop context: This is a {crop_name} leaf.\n\n" + DISEASE_ANALYSIS_PROMPT

        contents: List[Any] = [prompt]
        for filename, img_bytes in raw_files[:3]:
            mime = "image/jpeg"
            if filename.lower().endswith(".png"):
                mime = "image/png"
            elif filename.lower().endswith(".webp"):
                mime = "image/webp"
            part = types.Part.from_bytes(data=img_bytes, mime_type=mime)
            contents.append(part)

        if len(contents) < 2:
            return None

        logger.info("Calling Gemini evidence-first disease analysis for crop '%s' (%d images).", crop_name, len(raw_files))
        
        candidate_models = [model_name or "gemini-flash-latest", "gemini-flash-latest", "gemini-2.0-flash", "gemini-1.5-flash"]
        response = None
        for m in candidate_models:
            try:
                response = client.models.generate_content(
                    model=m,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                if response and response.text:
                    break
            except Exception as ex:
                logger.debug("Model %s failed for disease analysis: %s", m, ex)
                continue

        if not response or not response.text:
            return None

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        parsed = json.loads(raw_text)

        category = parsed.get("category", "UNKNOWN_UNCERTAIN").strip().upper()
        disease_name = parsed.get("disease_name", "Unknown Condition").strip()
        confidence = float(parsed.get("confidence", 0.0))

        # Parse visual evidence block
        ve_raw = parsed.get("visual_evidence", {})
        visual_evidence = VisualEvidenceDetail(
            directly_visible=ve_raw.get("directly_visible", []),
            inferred=ve_raw.get("inferred", []),
            unavailable=ve_raw.get("unavailable", []),
            dominant_morphology=ve_raw.get("dominant_morphology", "UNSPECIFIED")
        )

        # Parse candidates
        raw_candidates = parsed.get("candidates", [])
        candidates = []
        for c in raw_candidates[:4]:
            c_name = c.get("name", "")
            c_cat = c.get("category", "UNKNOWN_UNCERTAIN").upper()
            c_conf = float(c.get("confidence", 0.0))
            c_ematch = float(c.get("evidence_match_score", c_conf))
            if c_name:
                candidates.append(
                    DiseaseCandidate(
                        disease_name=c_name,
                        category=c_cat,
                        confidence=c_conf,
                        evidence_match_score=c_ematch
                    )
                )

        logger.info(
            "Gemini evidence-first result: Category=%s, Name='%s', Conf=%.2f, VisualFeatures=%d",
            category, disease_name, confidence, len(visual_evidence.directly_visible)
        )

        return NormalizedDiseaseResult(
            disease_name=disease_name,
            category=category,
            confidence=confidence,
            calibrated_confidence=confidence,  # Will be calibrated by diagnosis_validator
            provider_name="Gemini Vision (Evidence-First VLM)",
            is_mock=False,
            supported=True,
            candidates=candidates,
            visual_evidence=visual_evidence,
            provider_status="OK",
            error_message=None
        )

    except Exception as e:
        logger.error("Gemini evidence-first disease analysis failed: %s", str(e))
        return None

