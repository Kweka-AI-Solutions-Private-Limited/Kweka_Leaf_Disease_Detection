"""
host_pest_knowledge.py — Evidence-Backed Host-Pest Biological Compatibility Knowledge Base
--------------------------------------------------------------------------------------------
Provides biologically curated, evidence-backed host-pest relationships.
Evaluates biological plausibility between host crop identities and insect pest observations.

Guiding Principles:
  1. Used ONLY to evaluate biological plausibility, NEVER to overwrite model predictions.
  2. If a host relationship is unmapped or incomplete, returns UNKNOWN, NOT INCOMPATIBLE.
  3. Never change Potato to Bean merely because the insect is a bean pest.
  4. Never replace a low-confidence insect with an alternative pest.
  5. Provenance, botanical families, and biological limitations are explicitly documented.
"""

from typing import Dict, List, Optional, Any, Tuple
from schemas.cross_validation import (
    HostPestRelationshipType,
    HostPestCompatibilityStatus,
    HostPestCompatibilityResult,
)


# Master Biological Knowledge Base for Agricultural Pests & Host Crops
# Sourced from EPPO Global Database, CABI Invasive Species Compendium, and IP102 Benchmark Taxonomy
HOST_PEST_PROFILES: Dict[str, Dict[str, Any]] = {
    "colorado potato beetle": {
        "canonical_name": "Colorado Potato Beetle",
        "scientific_name": "Leptinotarsa decemlineata",
        "order": "Coleoptera",
        "family": "Chrysomelidae",
        "established_hosts": ["potato", "solanum tuberosum", "tomato", "solanum lycopersicum", "brinjal / eggplant", "solanum melongena", "solanaceae"],
        "reported_hosts": ["bell pepper", "chilli / pepper", "capsicum annuum", "tobacco", "groundcherry"],
        "unexpected_hosts": ["rice", "wheat", "maize / corn", "cotton", "apple", "grape", "banana", "beans"],
        "provenance": "EPPO Data Sheets on Quarantine Pests; CABI Compendium (Leptinotarsa decemlineata)",
        "limitations": "Strictly oligophagous on solanaceous species; non-solanaceous feeding is biologically unexpected in nature.",
    },
    "leptinotarsa decemlineata": {
        "canonical_name": "Colorado Potato Beetle",
        "scientific_name": "Leptinotarsa decemlineata",
        "order": "Coleoptera",
        "family": "Chrysomelidae",
        "established_hosts": ["potato", "solanum tuberosum", "tomato", "solanum lycopersicum", "brinjal / eggplant", "solanum melongena", "solanaceae"],
        "reported_hosts": ["bell pepper", "chilli / pepper", "capsicum annuum", "tobacco", "groundcherry"],
        "unexpected_hosts": ["rice", "wheat", "maize / corn", "cotton", "apple", "grape", "banana", "beans"],
        "provenance": "EPPO Data Sheets on Quarantine Pests; CABI Compendium (Leptinotarsa decemlineata)",
        "limitations": "Strictly oligophagous on solanaceous species; non-solanaceous feeding is biologically unexpected in nature.",
    },
    "bean leaf beetle": {
        "canonical_name": "Bean Leaf Beetle",
        "scientific_name": "Cerotoma trifurcata",
        "order": "Coleoptera",
        "family": "Chrysomelidae",
        "established_hosts": ["beans", "soybean", "glycine max", "green gram / moong", "black gram / urad", "fabaceae", "leguminosae"],
        "reported_hosts": ["cowpea", "snap bean", "clover", "alfalfa", "pea"],
        "unexpected_hosts": ["potato", "tomato", "rice", "wheat", "maize / corn", "apple", "citrus"],
        "provenance": "USDA Agricultural Research Service; CABI Compendium (Cerotoma trifurcata)",
        "limitations": "Primarily feeds on legumes (Fabaceae); unexpected as a colonizing pest on Solanaceae (potato).",
    },
    "fall armyworm": {
        "canonical_name": "Fall Armyworm",
        "scientific_name": "Spodoptera frugiperda",
        "order": "Lepidoptera",
        "family": "Noctuidae",
        "established_hosts": ["maize / corn", "zea mays", "sorghum / jowar", "rice / paddy", "sugarcane", "poaceae"],
        "reported_hosts": ["cotton", "soybean", "groundnut / peanut", "potato", "tomato", "cabbage"],
        "unexpected_hosts": ["apple", "grape", "citrus"],
        "provenance": "FAO Fall Armyworm Technical Brief; CABI Compendium (Spodoptera frugiperda)",
        "limitations": "Highly polyphagous across grasses (Poaceae) with secondary hosts across multiple families.",
    },
    "cotton bollworm": {
        "canonical_name": "Cotton Bollworm / Corn Earworm",
        "scientific_name": "Helicoverpa armigera",
        "order": "Lepidoptera",
        "family": "Noctuidae",
        "established_hosts": ["cotton", "gossypium", "tomato", "chickpea / gram", "pigeon pea / arhar", "maize / corn"],
        "reported_hosts": ["soybean", "chilli / pepper", "okra / bhindi", "tobacco", "sunflower"],
        "unexpected_hosts": ["rice", "sugarcane"],
        "provenance": "CABI Compendium (Helicoverpa armigera); EPPO Global Database",
        "limitations": "Broad host range across field crops, legumes, and solanaceous vegetables.",
    },
    "rice leaf roller": {
        "canonical_name": "Rice Leaf Roller",
        "scientific_name": "Cnaphalocrocis medinalis",
        "order": "Lepidoptera",
        "family": "Crambidae",
        "established_hosts": ["rice / paddy", "oryza sativa"],
        "reported_hosts": ["wheat", "maize / corn", "sorghum / jowar", "pearl millet / bajra", "sugarcane"],
        "unexpected_hosts": ["potato", "tomato", "cotton", "apple", "mango", "citrus"],
        "provenance": "IRRI Rice Knowledge Bank; IP102 Benchmark Taxonomy",
        "limitations": "Oligophagous on graminaceous hosts (Poaceae). Non-grass hosts are biologically unexpected.",
    },
    "yellow rice borer": {
        "canonical_name": "Yellow Rice Borer",
        "scientific_name": "Scirpophaga incertulas",
        "order": "Lepidoptera",
        "family": "Crambidae",
        "established_hosts": ["rice / paddy", "oryza sativa"],
        "reported_hosts": ["wild rice"],
        "unexpected_hosts": ["potato", "tomato", "cotton", "maize / corn", "wheat", "mango", "citrus", "beans"],
        "provenance": "IRRI Rice Knowledge Bank; CABI Compendium (Scirpophaga incertulas)",
        "limitations": "Monophagous on Oryza species. Any non-rice host indicates an unexpected mismatch.",
    },
    "asiatic rice borer": {
        "canonical_name": "Asiatic Rice Borer",
        "scientific_name": "Chilo suppressalis",
        "order": "Lepidoptera",
        "family": "Crambidae",
        "established_hosts": ["rice / paddy", "oryza sativa"],
        "reported_hosts": ["maize / corn", "sugarcane", "sorghum / jowar"],
        "unexpected_hosts": ["potato", "tomato", "cotton", "apple", "grape", "beans"],
        "provenance": "CABI Compendium (Chilo suppressalis)",
        "limitations": "Gramineous stem borer. Incompatible with dicotyledonous crops.",
    },
    "brown plant hopper": {
        "canonical_name": "Brown Plant Hopper",
        "scientific_name": "Nilaparvata lugens",
        "order": "Hemiptera",
        "family": "Delphacidae",
        "established_hosts": ["rice / paddy", "oryza sativa"],
        "reported_hosts": ["wild rice"],
        "unexpected_hosts": ["potato", "tomato", "cotton", "wheat", "maize / corn", "apple", "beans"],
        "provenance": "IRRI Rice Knowledge Bank; EPPO Global Database",
        "limitations": "Strictly monophagous sap-sucking planthopper of rice tillers.",
    },
    "green peach aphid": {
        "canonical_name": "Green Peach Aphid",
        "scientific_name": "Myzus persicae",
        "order": "Hemiptera",
        "family": "Aphididae",
        "established_hosts": ["potato", "peach", "tomato", "chilli / pepper", "cabbage", "cauliflower"],
        "reported_hosts": ["tobacco", "spinach", "pea", "eggplant", "cotton"],
        "unexpected_hosts": ["rice", "sugarcane"],
        "provenance": "CABI Compendium (Myzus persicae)",
        "limitations": "Extremely polyphagous secondary host range, but rarely establishes colonizing populations on paddy.",
    },
    "tobacco whitefly": {
        "canonical_name": "Tobacco Whitefly / Silverleaf Whitefly",
        "scientific_name": "Bemisia tabaci",
        "order": "Hemiptera",
        "family": "Aleyrodidae",
        "established_hosts": ["cotton", "tomato", "potato", "brinjal / eggplant", "chilli / pepper", "cucurbits"],
        "reported_hosts": ["soybean", "okra / bhindi", "cassava", "beans"],
        "unexpected_hosts": ["rice", "wheat"],
        "provenance": "CABI Compendium (Bemisia tabaci)",
        "limitations": "Broad host range across hundreds of dicotyledonous species.",
    },
    "whitefly": {
        "canonical_name": "Tobacco Whitefly / Silverleaf Whitefly",
        "scientific_name": "Bemisia tabaci",
        "order": "Hemiptera",
        "family": "Aleyrodidae",
        "established_hosts": ["cotton", "tomato", "potato", "brinjal / eggplant", "chilli / pepper", "cucurbits"],
        "reported_hosts": ["soybean", "okra / bhindi", "cassava", "beans"],
        "unexpected_hosts": ["rice", "wheat"],
        "provenance": "CABI Compendium (Bemisia tabaci)",
        "limitations": "Broad host range across hundreds of dicotyledonous species.",
    },
    "tiger longicorn beetle": {
        "canonical_name": "Tiger Longicorn Beetle (Coffee Stem Borer)",
        "scientific_name": "Xylotrechus quadripes",
        "order": "Coleoptera",
        "family": "Cerambycidae",
        "established_hosts": ["coffee", "coffea arabica"],
        "reported_hosts": ["teak", "gardenia"],
        "unexpected_hosts": ["rice", "wheat", "potato", "tomato", "cabbage", "cotton"],
        "provenance": "Central Coffee Research Institute (CCRI); IP102 Benchmark Catalog",
        "limitations": "Strict woody perennial stem borer of coffee; completely unexpected on herbaceous foliage.",
    },
    "xylotrechus": {
        "canonical_name": "Tiger Longicorn Beetle (Coffee Stem Borer)",
        "scientific_name": "Xylotrechus quadripes",
        "order": "Coleoptera",
        "family": "Cerambycidae",
        "established_hosts": ["coffee", "coffea arabica"],
        "reported_hosts": ["teak", "gardenia"],
        "unexpected_hosts": ["rice", "wheat", "potato", "tomato", "cabbage", "cotton"],
        "provenance": "Central Coffee Research Institute (CCRI); IP102 Benchmark Catalog",
        "limitations": "Strict woody perennial stem borer of coffee; completely unexpected on herbaceous foliage.",
    },
    "mango flat beak leafhopper": {
        "canonical_name": "Mango Flat Beak Leafhopper",
        "scientific_name": "Idioscopus spp.",
        "order": "Hemiptera",
        "family": "Cicadellidae",
        "established_hosts": ["mango", "mangifera indica"],
        "reported_hosts": [],
        "unexpected_hosts": ["rice", "wheat", "potato", "cotton", "tomato"],
        "provenance": "ICAR-Central Institute for Subtropical Horticulture; IP102 Benchmark Catalog",
        "limitations": "Oligophagous pest of mango inflorescence and flush foliage.",
    },
    "citrus red mite": {
        "canonical_name": "Citrus Red Mite",
        "scientific_name": "Panonychus citri",
        "order": "Trombidiformes",
        "family": "Tetranychidae",
        "established_hosts": ["citrus", "orange", "lemon", "lime"],
        "reported_hosts": ["papaya", "rose"],
        "unexpected_hosts": ["rice", "wheat", "potato"],
        "provenance": "University of California IPM Guidelines; IP102 Benchmark Catalog",
        "limitations": "Primary foliage pest of Rutaceae (citrus).",
    },
    "panonchus citri": {
        "canonical_name": "Citrus Red Mite",
        "scientific_name": "Panonychus citri",
        "order": "Trombidiformes",
        "family": "Tetranychidae",
        "established_hosts": ["citrus", "orange", "lemon", "lime"],
        "reported_hosts": ["papaya", "rose"],
        "unexpected_hosts": ["rice", "wheat", "potato"],
        "provenance": "University of California IPM Guidelines; IP102 Benchmark Catalog",
        "limitations": "Primary foliage pest of Rutaceae (citrus).",
    },
}


# Family and crop normalization mappings for robust biological lookup
CROP_FAMILY_MAP: Dict[str, str] = {
    "potato": "Solanaceae",
    "tomato": "Solanaceae",
    "brinjal / eggplant": "Solanaceae",
    "chilli / pepper": "Solanaceae",
    "rice / paddy": "Poaceae",
    "wheat": "Poaceae",
    "maize / corn": "Poaceae",
    "sorghum / jowar": "Poaceae",
    "pearl millet / bajra": "Poaceae",
    "sugarcane": "Poaceae",
    "beans": "Fabaceae",
    "soybean": "Fabaceae",
    "chickpea / gram": "Fabaceae",
    "pigeon pea / arhar": "Fabaceae",
    "groundnut / peanut": "Fabaceae",
    "cotton": "Malvaceae",
    "okra / bhindi": "Malvaceae",
    "cabbage": "Brassicaceae",
    "cauliflower": "Brassicaceae",
    "mustard / rapeseed": "Brassicaceae",
    "coffee": "Rubiaceae",
    "tea": "Theaceae",
    "mango": "Anacardiaceae",
    "apple": "Rosaceae",
    "pear": "Rosaceae",
    "grape": "Vitaceae",
    "citrus": "Rutaceae",
    "lemon": "Rutaceae",
    "orange": "Rutaceae",
}


def _clean_str(s: Optional[str]) -> str:
    if not s:
        return ""
    return s.strip().lower()


def find_pest_profile(pest_name: str) -> Optional[Dict[str, Any]]:
    """Resolves pest metadata by exact match, scientific name, or substring."""
    clean = _clean_str(pest_name)
    if not clean:
        return None

    # 1. Direct key match
    if clean in HOST_PEST_PROFILES:
        return HOST_PEST_PROFILES[clean]

    # 2. Check canonical and scientific names
    for key, profile in HOST_PEST_PROFILES.items():
        if clean == _clean_str(profile.get("canonical_name")) or clean == _clean_str(profile.get("scientific_name")):
            return profile

    # 3. Substring matching
    for key, profile in HOST_PEST_PROFILES.items():
        if key in clean or clean in key:
            return profile
        if _clean_str(profile.get("canonical_name")) in clean:
            return profile

    return None


def evaluate_host_pest_compatibility(
    crop_name: Optional[str],
    pest_name: Optional[str],
    crop_status: Optional[str] = None,
    crop_confidence: Optional[float] = None,
) -> HostPestCompatibilityResult:
    """
    Evaluates biological compatibility between a candidate crop and candidate pest.
    Strict biological rules:
      - If crop or pest is missing/empty: UNKNOWN / NOT_APPLICABLE.
      - If pest is known and crop is in established_hosts: COMPATIBLE (ESTABLISHED_HOST).
      - If host crop confidence <= 70% or crop status is UNCERTAIN/SUSPECTED:
        Mark as UNCERTAIN_RELATIONSHIP; cannot claim confirmed host corroboration.
      - If pest is known and crop is in reported_hosts: COMPATIBLE (REPORTED_HOST).
      - If pest is known and crop is in unexpected_hosts: INCOMPATIBLE (UNEXPECTED_HOST).
      - If relationship is not documented in database: UNKNOWN (UNCERTAIN_RELATIONSHIP).
        NEVER default an unmapped crop to INCOMPATIBLE.
    """
    clean_crop = _clean_str(crop_name)
    clean_pest = _clean_str(pest_name)

    # Base case: Missing crop or pest
    if not clean_pest or clean_pest in ("unknown", "none", "no pest detected", "unidentified"):
        return HostPestCompatibilityResult(
            compatibility_status=HostPestCompatibilityStatus.NOT_APPLICABLE,
            pest_canonical_name=pest_name,
            host_crop_name=crop_name,
            relationship_type=HostPestRelationshipType.NOT_EVALUATED,
            relationship_provenance=None,
            biological_family=None,
            notes="No insect pest candidate specified for host compatibility evaluation.",
        )

    if not clean_crop or clean_crop in ("unknown", "unidentified", "unspecified", "none"):
        return HostPestCompatibilityResult(
            compatibility_status=HostPestCompatibilityStatus.UNKNOWN,
            pest_canonical_name=pest_name,
            host_crop_name=crop_name,
            relationship_type=HostPestRelationshipType.UNCERTAIN_RELATIONSHIP,
            relationship_provenance=None,
            biological_family=None,
            notes=f"Host crop is unknown or unspecified. Cannot verify biological plausibility for pest '{pest_name}'.",
        )

    profile = find_pest_profile(clean_pest)
    if not profile:
        # Pest is outside the curated knowledge base -> must return UNKNOWN, NOT INCOMPATIBLE
        return HostPestCompatibilityResult(
            compatibility_status=HostPestCompatibilityStatus.UNKNOWN,
            pest_canonical_name=pest_name,
            host_crop_name=crop_name,
            relationship_type=HostPestRelationshipType.UNCERTAIN_RELATIONSHIP,
            relationship_provenance="Incomplete Biological Database",
            biological_family=CROP_FAMILY_MAP.get(clean_crop),
            notes=(
                f"Pest candidate '{pest_name}' is not documented in the biological compatibility catalog. "
                f"Relationship with host '{crop_name}' is UNKNOWN (catalog is incomplete; absence is not proof of incompatibility)."
            ),
        )

    canonical = profile["canonical_name"]
    sci = profile.get("scientific_name")
    established = [_clean_str(h) for h in profile.get("established_hosts", [])]
    reported = [_clean_str(h) for h in profile.get("reported_hosts", [])]
    unexpected = [_clean_str(h) for h in profile.get("unexpected_hosts", [])]
    provenance = profile.get("provenance")
    crop_family = CROP_FAMILY_MAP.get(clean_crop, "")
    clean_family = _clean_str(crop_family)

    # Check whether crop identity is unconfirmed (confidence <= 70% or UNCERTAIN/SUSPECTED status)
    crop_is_unconfirmed = (
        (crop_confidence is not None and crop_confidence <= 0.70) or
        (crop_status is not None and str(crop_status).upper() in ("UNCERTAIN", "SUSPECTED", "NEEDS_VERIFICATION"))
    )

    # Check 1: Established Host
    is_established = any(h in clean_crop or clean_crop in h for h in established)
    if not is_established and clean_family:
        is_established = any(h == clean_family for h in established)

    if is_established:
        if crop_is_unconfirmed:
            conf_str = f"{crop_confidence * 100:.1f}%" if crop_confidence is not None else "low"
            return HostPestCompatibilityResult(
                compatibility_status=HostPestCompatibilityStatus.UNKNOWN,
                pest_canonical_name=canonical,
                pest_scientific_name=sci,
                host_crop_name=crop_name,
                relationship_type=HostPestRelationshipType.UNCERTAIN_RELATIONSHIP,
                relationship_provenance=provenance,
                biological_family=crop_family or None,
                notes=(
                    f"Conditional pairing: '{canonical}' is a known pest of '{crop_name}', BUT host crop identity "
                    f"is unconfirmed ({conf_str} confidence, at or below 70% threshold). This biological pairing "
                    f"is contingent on unverified host identity and cannot be used to corroborate or confirm the insect species."
                ),
            )
        return HostPestCompatibilityResult(
            compatibility_status=HostPestCompatibilityStatus.COMPATIBLE,
            pest_canonical_name=canonical,
            pest_scientific_name=sci,
            host_crop_name=crop_name,
            relationship_type=HostPestRelationshipType.ESTABLISHED_HOST,
            relationship_provenance=provenance,
            biological_family=crop_family or None,
            notes=f"Biologically compatible: '{canonical}' is a well-established pest of confirmed host crop '{crop_name}'.",
        )

    # Check 2: Reported / Secondary Host
    is_reported = any(h in clean_crop or clean_crop in h for h in reported)
    if not is_reported and clean_family:
        is_reported = any(h == clean_family for h in reported)

    if is_reported:
        if crop_is_unconfirmed:
            conf_str = f"{crop_confidence * 100:.1f}%" if crop_confidence is not None else "low"
            return HostPestCompatibilityResult(
                compatibility_status=HostPestCompatibilityStatus.UNKNOWN,
                pest_canonical_name=canonical,
                pest_scientific_name=sci,
                host_crop_name=crop_name,
                relationship_type=HostPestRelationshipType.UNCERTAIN_RELATIONSHIP,
                relationship_provenance=provenance,
                biological_family=crop_family or None,
                notes=(
                    f"Conditional pairing: '{canonical}' is documented as secondary on '{crop_name}', BUT host crop identity "
                    f"is unconfirmed ({conf_str} confidence). This pairing cannot be used to confirm the insect species."
                ),
            )
        return HostPestCompatibilityResult(
            compatibility_status=HostPestCompatibilityStatus.COMPATIBLE,
            pest_canonical_name=canonical,
            pest_scientific_name=sci,
            host_crop_name=crop_name,
            relationship_type=HostPestRelationshipType.REPORTED_HOST,
            relationship_provenance=provenance,
            biological_family=crop_family or None,
            notes=f"Biologically compatible: '{canonical}' is documented as a reported/secondary host for confirmed '{crop_name}'.",
        )

    # Check 3: Unexpected Host (Specific known incompatible pairing)
    is_unexpected = any(h in clean_crop or clean_crop in h for h in unexpected)
    if is_unexpected:
        return HostPestCompatibilityResult(
            compatibility_status=HostPestCompatibilityStatus.INCOMPATIBLE,
            pest_canonical_name=canonical,
            pest_scientific_name=sci,
            host_crop_name=crop_name,
            relationship_type=HostPestRelationshipType.UNEXPECTED_HOST,
            relationship_provenance=provenance,
            biological_family=crop_family or None,
            notes=(
                f"Biological host mismatch: '{canonical}' is cataloged as unexpected on '{crop_name}'. "
                f"Review both crop identification and insect prediction for potential misclassification."
            ),
        )

    # Check 4: Unmapped entry in incomplete database -> UNKNOWN
    return HostPestCompatibilityResult(
        compatibility_status=HostPestCompatibilityStatus.UNKNOWN,
        pest_canonical_name=canonical,
        pest_scientific_name=sci,
        host_crop_name=crop_name,
        relationship_type=HostPestRelationshipType.UNCERTAIN_RELATIONSHIP,
        relationship_provenance=provenance,
        biological_family=crop_family or None,
        notes=(
            f"Relationship between pest '{canonical}' and host '{crop_name}' is uncataloged in the reference database. "
            f"Retained as UNKNOWN. Do not treat unmapped entries as proof of biological impossibility."
        ),
    )
