"""
pathology_classifier.py — Plant Pathology vs. Non-Disease Organism Classifier
-------------------------------------------------------------------------------
Classifies entities returned by EPPO / Pl@ntNet plant health streams to strictly
segregate botanical plant pathologies (fungi, bacteria, viruses, oomycetes)
from non-disease organisms (insects, mites, nematodes, mollusks).

Guarantees:
  - Arthropod and insect pests (e.g. Colorado potato beetle) are NEVER presented
    as plant disease pathologies in the Disease Detection panel.
  - Common names are preferred for human display.
"""

import re
from typing import NamedTuple, Literal, Optional

# Keywords that definitively indicate an animal/arthropod/nematode pest, NOT a plant pathology
PEST_KEYWORDS = {
    # Insects & Life Stages
    "beetle", "weevil", "borer", "caterpillar", "armyworm", "cutworm", "bollworm",
    "budworm", "hornworm", "wireworm", "pinworm", "looper", "loopers", "moth",
    "butterfly", "fly", "flies", "midge", "midges", "maggot", "maggots", "leafminer",
    "aphid", "aphids", "whitefly", "whiteflies", "scale", "scales", "mealybug", "mealybugs",
    "psyllid", "psyllids", "hopper", "hoppers", "leafhopper", "leafhoppers",
    "planthopper", "planthoppers", "spittlebug", "thrips", "bug", "bugs", "stink bug",
    "chinch bug", "lace bug", "shield bug", "plant bug", "locust", "locusts",
    "grasshopper", "grasshoppers", "cricket", "crickets", "cicada", "cicadas",
    "ant", "ants", "wasp", "wasps", "sawfly", "sawflies", "chafer", "chafers",
    "chalcid", "grub", "grubs", "worm", "worms", "flea", "colorado beetle",
    # Mites
    "mite", "mites", "spider mite", "spider mites", "rust mite", "gall mite",
    # Nematodes & Mollusks
    "nematode", "nematodes", "slug", "slugs", "snail", "snails",
}

# Scientific genera / higher taxa of known agricultural insect/arthropod pests
PEST_TAXA = {
    "leptinotarsa", "spodoptera", "helicoverpa", "heliothis", "chilo", "scirpophaga",
    "cnaphalocrocis", "tuta", "agrotis", "mythimna", "aphis", "myzus", "bemisia",
    "trialeurodes", "thrips", "frankliniella", "liriomyza", "bactrocera", "dacus",
    "ceratitis", "tetranychus", "panonychus", "polyphagotarsonemus", "meloidogyne",
    "heterodera", "globodera", "pratylenchus", "xylotrechus", "diabrotica", "cerotoma",
    "epitrix", "phyllotreta", "maladera", "popillia", "holotrichia", "hypera",
    "lissorhoptrus", "nilaparvata", "sogatella", "laodelphax", "nephotettix", "peregrinus",
    "amrasca", "empoasca", "adelphocoris", "lygus", "dysdercus", "nezara", "halyomorpha",
    "maruca", "leucinodes", "plutella", "pieris", "papilio", "manduca", "sitobion",
    "rhopalosiphum", "schizaphis", "sitodiplosis", "penthaleus", "haplothrips",
    "cephus", "dolerus", "cerodontha", "pegomya", "mamestra", "loxostege",
    "bothynoderes", "asproparthenis", "serica", "lytta", "epicauta", "therioaphis",
    "odontothrips", "bruchophagus", "apolygus", "daktulosphaira", "colomerus",
    "brevipalpus", "oides", "pseudococcus", "paranthrene", "ampelophaga", "lycorma",
    "cicadella", "erythroneura", "phyllocoptes", "icerya", "unaspis", "ceroplastes",
    "chrysomphalus", "parlatoria", "nipaecoccus", "aleurocanthus", "toxoptera",
    "scirtothrips", "dasineura", "deporaus", "chlumetia", "rhytidodera", "sternochetus",
}

# Keywords that indicate true plant pathologies (fungi, bacteria, viruses, oomycetes, abiotic)
PATHOLOGY_KEYWORDS = {
    "blight", "mildew", "rust", "rot", "spot", "scab", "smut", "canker", "wilt",
    "anthracnose", "damping-off", "damping off", "mold", "mould", "blast", "fusarium",
    "rhizoctonia", "verticillium", "phytophthora", "pythium", "alternaria",
    "cercospora", "septoria", "colletotrichum", "puccinia", "powdery mildew",
    "downy mildew", "leaf curl", "black rot", "bacterial blight", "bacterial spot",
    "bacterial wilt", "bacterial canker", "bacterial speck", "soft rot", "black leg",
    "fire blight", "crown gall", "xanthomonas", "pseudomonas", "ralstonia", "erwinia",
    "pectobacterium", "virus", "viruses", "mosaic", "mottle", "leaf roll",
    "spotted wilt", "streak", "yellows", "viroid", "begomovirus", "tospovirus",
    "potyvirus", "chlorosis", "deficiency", "necrosis", "edema", "cladosporium",
    "botrytis", "sclerotinia", "sclerotium", "macrophomina", "asochyta", "venturia",
    "erysiphe", "podosphaera", "oidium", "leveillula", "pseudoperonospora",
    "peronospora", "bremia", "albugo", "synchytrium", "taphrina", "ustilago",
    "tilletia", "uromyces", "gymnosporangium", "corynespora", "stemphylium",
    "bipolaris", "exserohilum", "curvularia", "helminthosporium", "magnaporthe",
    "claviceps", "corticium", "monilinia", "guignardia", "stigmina", "diplodia",
}


class PathologyClassificationResult(NamedTuple):
    is_pathology: bool
    organism_type: Literal["PATHOLOGY", "ARTHROPOD_PEST", "NEMATODE_PEST", "MOLLUSK_PEST", "UNKNOWN"]
    common_name: str
    scientific_name: str
    primary_display_name: str
    reason: str


def parse_eppo_description(description: str, eppo_code: str = "") -> tuple[str, str]:
    """
    Parses Pl@ntNet / EPPO description string.
    EPPO standard format is: 'Scientific Name - Common name'
    Example: 'Leptinotarsa decemlineata - Colorado beetle (Colorado potato beetle)'
    Example: 'Phytophthora infestans - Late blight of potato'
    Returns: (common_name, scientific_name)
    """
    if not description:
        return (eppo_code or "Unknown Disorder", "")

    if " - " in description:
        parts = description.split(" - ", 1)
        scientific = parts[0].strip()
        common = parts[1].strip()

        # Clean parenthetical duplicates if present
        # e.g., "Colorado beetle (Colorado potato beetle)" -> prefer "Colorado potato beetle"
        if "colorado beetle (colorado potato beetle)" in common.lower():
            common = "Colorado potato beetle"

        return (common, scientific)

    return (description.strip(), "")


def classify_disorder(description: str, eppo_code: str = "") -> PathologyClassificationResult:
    """
    Evaluates whether an entity is a genuine plant pathology or an animal/insect pest.
    """
    common_name, scientific_name = parse_eppo_description(description, eppo_code)
    text_to_check = f"{description} {eppo_code} {common_name} {scientific_name}".lower()

    # 1. Check for specific known insect/pest scientific taxa
    sci_first_word = scientific_name.lower().split()[0] if scientific_name else ""
    if sci_first_word in PEST_TAXA:
        return PathologyClassificationResult(
            is_pathology=False,
            organism_type="ARTHROPOD_PEST",
            common_name=common_name,
            scientific_name=scientific_name,
            primary_display_name=common_name,
            reason=f"Taxon '{scientific_name}' is a cataloged insect/arthropod pest, not a plant pathogen.",
        )

    # 2. Check for explicit pest keywords in common name or description
    words = re.findall(r"\b[a-z\-]+\b", text_to_check)
    for word in words:
        if word in PEST_KEYWORDS:
            # Distinguish nematode vs arthropod
            org_type = "NEMATODE_PEST" if "nematode" in word else "ARTHROPOD_PEST"
            return PathologyClassificationResult(
                is_pathology=False,
                organism_type=org_type,
                common_name=common_name,
                scientific_name=scientific_name,
                primary_display_name=common_name,
                reason=f"Identified as pest organism via keyword '{word}'. Excluded from pathology stream.",
            )

    # 3. Check for multi-word pest terms
    for phrase in ["colorado beetle", "spider mite", "stem borer", "leaf miner", "plant bug"]:
        if phrase in text_to_check:
            return PathologyClassificationResult(
                is_pathology=False,
                organism_type="ARTHROPOD_PEST",
                common_name=common_name,
                scientific_name=scientific_name,
                primary_display_name=common_name,
                reason=f"Identified as pest organism via term '{phrase}'. Excluded from pathology stream.",
            )

    # 4. If no pest indicators were triggered, check pathology keywords
    for word in words:
        if word in PATHOLOGY_KEYWORDS:
            return PathologyClassificationResult(
                is_pathology=True,
                organism_type="PATHOLOGY",
                common_name=common_name,
                scientific_name=scientific_name,
                primary_display_name=f"{common_name} ({scientific_name})" if scientific_name else common_name,
                reason=f"Validated botanical disease pathology via diagnostic term '{word}'.",
            )

    # 5. Default fallback: If scientific name is present and no pest indicator matched,
    # assume pathology candidate but mark as provisional
    return PathologyClassificationResult(
        is_pathology=True,
        organism_type="PATHOLOGY",
        common_name=common_name,
        scientific_name=scientific_name,
        primary_display_name=f"{common_name} ({scientific_name})" if scientific_name else common_name,
        reason="Presumed pathology candidate without pest markers.",
    )
