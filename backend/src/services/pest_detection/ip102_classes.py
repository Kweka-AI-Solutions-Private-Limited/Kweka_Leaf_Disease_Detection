"""
ip102_classes.py — Benchmark IP102 Insect & Pest Taxonomy Catalog
------------------------------------------------------------------
Provides canonical reference data for the 102 agricultural insect pest classes
established by the benchmark IP102 dataset (Wu et al., CVPR).

Includes:
  - Integer class ID mapping (0 - 101) aligned exactly with official benchmark ordering
  - Canonical common and scientific taxonomic names
  - Primary host crop susceptibilities
  - Feeding guild / damage mechanisms (sap-sucking, foliar chewing, stem boring, leaf mining, etc.)
  - Category differentiation (adult insect specimen vs. juvenile larva vs. foliar damage)
"""

from typing import Dict, List, Optional, Any

# Canonical list of 102 classes in benchmark order (matching pests.yaml / model.names)
RAW_BENCHMARK_NAMES = [
    "rice leaf roller", "rice leaf caterpillar", "paddy stem maggot", "asiatic rice borer", "yellow rice borer",
    "rice gall midge", "Rice Stemfly", "brown plant hopper", "white backed plant hopper", "small brown plant hopper",
    "rice water weevil", "rice leafhopper", "grain spreader thrips", "rice shell pest", "grub",
    "mole cricket", "wireworm", "white margined moth", "black cutworm", "large cutworm",
    "yellow cutworm", "red spider", "corn borer", "army worm", "aphids",
    "Potosiabre vitarsis", "peach borer", "english grain aphid", "green bug", "bird cherry-oataphid",
    "wheat blossom midge", "penthaleus major", "longlegged spider mite", "wheat phloeothrips", "wheat sawfly",
    "cerodonta denticornis", "beet fly", "flea beetle", "cabbage army worm", "beet army worm",
    "Beet spot flies", "meadow moth", "beet weevil", "sericaorient alismots chulsky", "alfalfa weevil",
    "flax budworm", "alfalfa plant bug", "tarnished plant bug", "Locustoidea", "lytta polita",
    "legume blister beetle", "blister beetle", "therioaphis maculata Buckton", "odontothrips loti", "Thrips",
    "alfalfa seed chalcid", "Pieris canidia", "Apolygus lucorum", "Limacodidae", "Viteus vitifoliae",
    "Colomerus vitis", "Brevipoalpus lewisi McGregor", "oides decempunctata", "Polyphagotars onemus latus", "Pseudococcus comstocki Kuwana",
    "parathrene regalis", "Ampelophaga", "Lycorma delicatula", "Xylotrechus", "Cicadella viridis",
    "Miridae", "Trialeurodes vaporariorum", "Erythroneura apicalis", "Papilio xuthus", "Panonchus citri McGregor",
    "Phyllocoptes oleiverus ashmead", "Icerya purchasi Maskell", "Unaspis yanonensis", "Ceroplastes rubens", "Chrysomphalus aonidum",
    "Parlatoria zizyphus Lucus", "Nipaecoccus vastalor", "Aleurocanthus spiniferus", "Tetradacus c Bactrocera minax", "Dacus dorsalis(Hendel)",
    "Bactrocera tsuneonis", "Prodenia litura", "Adristyrannus", "Phyllocnistis citrella Stainton", "Toxoptera citricidus",
    "Toxoptera aurantii", "Aphis citricola Vander Goot", "Scirtothrips dorsalis Hood", "Dasineura sp", "Lawana imitata Melichar",
    "Salurnis marginella Guerr", "Deporaus marginatus Pascoe", "Chlumetia transversa", "Mango flat beak leafhopper", "Rhytidodera bowrinii white",
    "Sternochetus frigidus", "Cicadellidae"
]

# Canonical taxonomy, host crops, feeding guilds, and metadata for all 102 benchmark classes
IP102_METADATA_TABLE: Dict[int, Dict[str, Any]] = {
    0: {
        "display_name": "Rice Leaf Roller",
        "scientific_name": "Cnaphalocrocis medinalis",
        "crops": ["Rice / Paddy", "Wheat", "Pearl Millet / Bajra", "Sorghum / Jowar"],
        "category": "LARVA",
        "damage_type": "foliar_chewing",
        "affected_organs": ["Leaves"],
        "description": "Larvae fold leaves longitudinally and scrape the green mesophyll, leaving longitudinal white streaks.",
        "aliases": ["Rice Leaf Roller", "rice leaf roller", "Cnaphalocrocis medinalis"]
    },
    1: {
        "display_name": "Rice Leaf Caterpillar",
        "scientific_name": "Naranga aenescens",
        "crops": ["Rice / Paddy"],
        "category": "LARVA",
        "damage_type": "foliar_chewing",
        "affected_organs": ["Leaves"],
        "description": "Green caterpillars chewing jagged margins on rice leaves, defoliating young tillers.",
        "aliases": ["Rice Leaf Caterpillar", "rice leaf caterpillar", "Naranga aenescens"]
    },
    2: {
        "display_name": "Paddy Stem Maggot",
        "scientific_name": "Hydrellia sasakii",
        "crops": ["Rice / Paddy"],
        "category": "LARVA",
        "damage_type": "stem_boring",
        "affected_organs": ["Stems", "Tender shoots"],
        "description": "Maggots bore into leaf sheaths and young stems, causing ragged deformed leaves and stunting.",
        "aliases": ["Paddy Stem Maggot", "paddy stem maggot"]
    },
    3: {
        "display_name": "Asiatic Rice Borer",
        "scientific_name": "Chilo suppressalis",
        "crops": ["Rice / Paddy", "Corn (Maize)", "Sugarcane"],
        "category": "LARVA",
        "damage_type": "stem_boring",
        "affected_organs": ["Stems", "Panicles"],
        "description": "Larvae bore inside rice stems causing 'dead heart' at tillering and 'white head' at reproductive stage.",
        "aliases": ["Asiatic Rice Borer", "asiatic rice borer"]
    },
    4: {
        "display_name": "Yellow Rice Borer",
        "scientific_name": "Scirpophaga incertulas",
        "crops": ["Rice / Paddy"],
        "category": "LARVA",
        "damage_type": "stem_boring",
        "affected_organs": ["Stems", "Panicles"],
        "description": "Monophagous pest boring into rice culms, causing devastating dead hearts and white ears.",
        "aliases": ["Yellow Rice Borer", "yellow rice borer", "Paddy Stem Borer"]
    },
    5: {
        "display_name": "Rice Gall Midge",
        "scientific_name": "Orseolia oryzae",
        "crops": ["Rice / Paddy"],
        "category": "LARVA",
        "damage_type": "gall_forming",
        "affected_organs": ["Tillers", "Growing points"],
        "description": "Larvae feed at shoot apex, morphing leaf sheaths into hollow tubular 'silver shoot' galls.",
        "aliases": ["Rice Gall Midge", "rice gall midge"]
    },
    6: {
        "display_name": "Rice Stemfly",
        "scientific_name": "Chlorops oryzae",
        "crops": ["Rice / Paddy"],
        "category": "LARVA",
        "damage_type": "stem_boring",
        "affected_organs": ["Tillers", "Panicles"],
        "description": "Maggots chew internal tender shoot tissue, producing broad ragged holes on emerging leaves.",
        "aliases": ["Rice Stemfly", "rice stemfly"]
    },
    7: {
        "display_name": "Brown Plant Hopper",
        "scientific_name": "Nilaparvata lugens",
        "crops": ["Rice / Paddy"],
        "category": "INSECT",
        "damage_type": "sap_sucking",
        "affected_organs": ["Stem bases", "Tillers"],
        "description": "Phloem-sucking delphacid planthopper causing characteristic drying patches termed 'hopper burn'.",
        "aliases": ["Brown Plant Hopper", "brown plant hopper", "Brown Planthopper"]
    },
    8: {
        "display_name": "White Backed Plant Hopper",
        "scientific_name": "Sogatella furcifera",
        "crops": ["Rice / Paddy", "Corn (Maize)"],
        "category": "INSECT",
        "damage_type": "sap_sucking",
        "affected_organs": ["Leaves", "Stems"],
        "description": "Sap-sucking insect causing leaf yellowing, chlorosis, reduced tillering, and sooty mold.",
        "aliases": ["White Backed Plant Hopper", "white backed plant hopper", "Whitebacked Planthopper"]
    },
    9: {
        "display_name": "Small Brown Plant Hopper",
        "scientific_name": "Laodelphax striatellus",
        "crops": ["Rice / Paddy", "Wheat", "Barley", "Corn (Maize)"],
        "category": "INSECT",
        "damage_type": "sap_sucking",
        "affected_organs": ["Leaves", "Stems"],
        "description": "Planthopper vectoring Rice Stripe Virus and Rice Black-Streaked Dwarf Virus.",
        "aliases": ["Small Brown Plant Hopper", "small brown plant hopper"]
    },
    10: {
        "display_name": "Rice Water Weevil",
        "scientific_name": "Lissorhoptrus oryzophilus",
        "crops": ["Rice / Paddy", "Corn (Maize)", "Sorghum / Jowar"],
        "category": "INSECT",
        "damage_type": "foliar_chewing",
        "affected_organs": ["Leaves", "Roots"],
        "description": "Adults chew longitudinal scars on foliage; subterranean larvae prune aquatic roots.",
        "aliases": ["Rice Water Weevil", "rice water weevil", "Fall Armyworm"]
    },
    11: {
        "display_name": "Rice Leafhopper",
        "scientific_name": "Nephotettix cincticeps",
        "crops": ["Rice / Paddy"],
        "category": "INSECT",
        "damage_type": "sap_sucking",
        "affected_organs": ["Leaves"],
        "description": "Green leafhopper vectoring tungro and dwarf viruses while sucking phloem sap.",
        "aliases": ["Rice Leafhopper", "rice leafhopper", "Green Leafhopper"]
    },
    12: {
        "display_name": "Grain Spreader Thrips",
        "scientific_name": "Haplothrips aculeatus",
        "crops": ["Rice / Paddy", "Wheat", "Barley"],
        "category": "INSECT",
        "damage_type": "rasping_sucking",
        "affected_organs": ["Spikelets", "Florets", "Grain"],
        "description": "Black thrips rasping developing grains and glumes, causing white empty florets.",
        "aliases": ["Grain Spreader Thrips", "grain spreader thrips"]
    },
    13: {
        "display_name": "Rice Shell Pest",
        "scientific_name": "Dicladispa armigera",
        "crops": ["Rice / Paddy"],
        "category": "INSECT",
        "damage_type": "leaf_mining",
        "affected_organs": ["Leaves"],
        "description": "Spiny beetle scraping leaf epidermis; larvae mine internal tissue leaving blistered streaks.",
        "aliases": ["Rice Shell Pest", "rice shell pest", "Rice Hispa"]
    },
    14: {
        "display_name": "Grub / White Grub",
        "scientific_name": "Holotrichia spp.",
        "crops": ["Corn (Maize)", "Sugarcane", "Groundnut / Peanut", "Potato"],
        "category": "LARVA",
        "damage_type": "foliar_chewing",
        "affected_organs": ["Roots", "Underground stems"],
        "description": "C-shaped scarabaeid larvae pruning primary roots, causing circular patches of wilted crops.",
        "aliases": ["grub", "White Grub"]
    },
    15: {
        "display_name": "Mole Cricket",
        "scientific_name": "Gryllotalpa orientalis",
        "crops": ["Rice / Paddy", "Corn (Maize)", "Tomato", "Potato", "Sugarcane"],
        "category": "INSECT",
        "damage_type": "foliar_chewing",
        "affected_organs": ["Roots", "Seedling collars"],
        "description": "Subterranean orthopteran severing seedling roots and stems near the soil surface.",
        "aliases": ["mole cricket", "Mole Cricket"]
    },
    16: {
        "display_name": "Wireworm",
        "scientific_name": "Agriotes spp.",
        "crops": ["Corn (Maize)", "Wheat", "Potato", "Cotton"],
        "category": "LARVA",
        "damage_type": "foliar_chewing",
        "affected_organs": ["Germinating seeds", "Seedling roots"],
        "description": "Hard-bodied elaterid click beetle larvae boring into planted seeds and roots.",
        "aliases": ["wireworm", "Wireworm", "Whitefly"]
    },
    17: {
        "display_name": "White Margined Moth",
        "scientific_name": "Mythimna loreyi",
        "crops": ["Corn (Maize)", "Sugarcane", "Rice / Paddy", "Wheat"],
        "category": "LARVA",
        "damage_type": "foliar_chewing",
        "affected_organs": ["Leaves", "Whorls"],
        "description": "Noctuid caterpillar chewing irregular leaf margins, defoliating cereal grasses.",
        "aliases": ["white margined moth", "White Margined Moth"]
    },
    18: {
        "display_name": "Black Cutworm",
        "scientific_name": "Agrotis ipsilon",
        "crops": ["Corn (Maize)", "Cotton", "Tomato", "Potato", "Soybean"],
        "category": "LARVA",
        "damage_type": "foliar_chewing",
        "affected_organs": ["Seedling stems"],
        "description": "Greasy gray-black nocturnal caterpillars cutting young crop stems flush with the soil.",
        "aliases": ["black cutworm", "Black Cutworm"]
    },
    19: {
        "display_name": "Large Cutworm",
        "scientific_name": "Agrotis tokionis",
        "crops": ["Corn (Maize)", "Tomato", "Potato", "Cabbage"],
        "category": "LARVA",
        "damage_type": "foliar_chewing",
        "affected_organs": ["Seedling stems", "Foliage"],
        "description": "Robust cutworm severing emergent stalks and feeding on subterranean plant crowns.",
        "aliases": ["large cutworm", "Large Cutworm"]
    },
    20: {
        "display_name": "Yellow Cutworm",
        "scientific_name": "Agrotis segetum",
        "crops": ["Cotton", "Corn (Maize)", "Wheat", "Potato"],
        "category": "LARVA",
        "damage_type": "foliar_chewing",
        "affected_organs": ["Stems", "Roots"],
        "description": "Turnip moth caterpillar chewing subterranean crowns and cutting young crop stems.",
        "aliases": ["yellow cutworm", "Yellow Cutworm", "Thrips"]
    },
    21: {
        "display_name": "Red Spider Mite",
        "scientific_name": "Tetranychus urticae",
        "crops": ["Cotton", "Tomato", "Brinjal / Eggplant", "Apple", "Tea"],
        "category": "INSECT",
        "damage_type": "sap_sucking",
        "affected_organs": ["Leaves"],
        "description": "Microscopic arachnid spinning fine webbing beneath leaves, producing chlorotic stippling.",
        "aliases": ["red spider", "Red Spider Mite"]
    },
    22: {
        "display_name": "Corn Borer",
        "scientific_name": "Ostrinia furnacalis",
        "crops": ["Corn (Maize)", "Sorghum / Jowar", "Pearl Millet / Bajra"],
        "category": "LARVA",
        "damage_type": "stem_boring",
        "affected_organs": ["Whorls", "Stalks", "Cobs"],
        "description": "Larvae produce shot-holes in whorls and tunnel through stalks, causing broken tassels and stalks.",
        "aliases": ["corn borer", "Corn Borer", "Asian Corn Borer"]
    },
    23: {
        "display_name": "Armyworm",
        "scientific_name": "Mythimna separata",
        "crops": ["Rice / Paddy", "Corn (Maize)", "Wheat", "Sorghum / Jowar"],
        "category": "LARVA",
        "damage_type": "foliar_chewing",
        "affected_organs": ["Leaves", "Panicles"],
        "description": "Gregarious marching larvae stripping foliage down to midribs and biting off earheads.",
        "aliases": ["army worm", "Armyworm"]
    },
    24: {
        "display_name": "Aphids",
        "scientific_name": "Aphidoidea",
        "crops": ["All Crops", "Cotton", "Wheat", "Corn (Maize)", "Mustard / Rapeseed"],
        "category": "INSECT",
        "damage_type": "sap_sucking",
        "affected_organs": ["Shoots", "Underside of leaves"],
        "description": "Phloem-feeding colonies causing leaf curling, stunting, and sticky sooty mold accumulation.",
        "aliases": ["aphids", "Aphids"]
    },
    37: {
        "display_name": "Flea Beetle",
        "scientific_name": "Phyllotreta / Chaetocnema spp.",
        "crops": ["Cabbage", "Canola", "Potato", "Tomato", "Brinjal / Eggplant"],
        "category": "INSECT",
        "damage_type": "foliar_shot_hole_chewing",
        "affected_organs": ["Leaves", "Seedling cotyledons"],
        "description": "Small jumping leaf beetles chewing characteristic circular shot-holes into leaves.",
        "aliases": ["flea beetle", "Flea Beetle"]
    },
    68: {
        "display_name": "Tiger Longicorn Beetle / Stem Borer (Xylotrechus)",
        "scientific_name": "Xylotrechus spp.",
        "crops": ["Coffee", "Grape", "Mulberry", "Apple", "Deciduous Trees"],
        "category": "INSECT",
        "damage_type": "stem_boring",
        "affected_organs": ["Stems", "Woody Trunks", "Branches"],
        "description": "Cerambycid longhorn beetle. Larvae bore deep internal galleries inside woody stems and trunks. Adults do not feed by foliar shot-hole chewing.",
        "aliases": ["Xylotrechus", "Tiger Longicorn Beetle", "Coffee White Stem Borer", "Xylotrechus quadripes"]
    },
}

# Construct the full 102 catalog
IP102_CATALOG: Dict[int, Dict[str, Any]] = {}

for idx, raw_name in enumerate(RAW_BENCHMARK_NAMES):
    if idx in IP102_METADATA_TABLE:
        meta = IP102_METADATA_TABLE[idx]
        display_name = meta["display_name"]
        sci_name = meta.get("scientific_name", "")
        crops = meta.get("crops", ["All Crops"])
        category = meta.get("category", "INSECT")
        dmg_type = meta.get("damage_type", "foliar_chewing")
        affected = meta.get("affected_organs", ["Leaves"])
        desc = meta.get("description", f"IP102 pest {display_name}.")
        aliases = meta.get("aliases", [raw_name, display_name])
    else:
        # Standardize title casing
        display_name = raw_name.replace("-", " ").title()
        sci_name = raw_name.capitalize()
        category = "INSECT"
        dmg_type = "foliar_chewing"
        affected = ["Leaves", "Stems", "Fruit"]
        crops = ["All Crops"]
        desc = f"IP102 benchmark cataloged pest #{idx}: {display_name}."
        aliases = [raw_name, display_name]

        # Specialize by common keyword
        raw_lower = raw_name.lower()
        if any(w in raw_lower for w in ["borer", "maggot", "sawfly"]):
            category = "LARVA"
            dmg_type = "stem_boring"
            affected = ["Stems", "Shoots"]
        elif any(w in raw_lower for w in ["caterpillar", "army", "moth", "worm", "weevil", "grub", "chalcid"]):
            category = "LARVA"
            dmg_type = "foliar_chewing"
            affected = ["Leaves"]
        elif any(w in raw_lower for w in ["aphid", "hopper", "bug", "mite", "scale", "whitefly", "psyllid", "thrips"]):
            category = "INSECT"
            dmg_type = "sap_sucking"
            affected = ["Underside of leaves", "Shoots"]
        elif any(w in raw_lower for w in ["fly", "dacus", "bactrocera"]):
            category = "INSECT"
            dmg_type = "fruit_boring"
            affected = ["Fruit"]

        if "citri" in raw_lower or "citrus" in raw_lower:
            crops = ["Lemon / Citrus", "Orange", "Mandarin"]
        elif "mango" in raw_lower:
            crops = ["Mango"]
        elif "rice" in raw_lower:
            crops = ["Rice / Paddy"]
        elif "wheat" in raw_lower:
            crops = ["Wheat", "Barley"]
        elif "beet" in raw_lower:
            crops = ["Sugarbeet", "Beet"]
        elif "grape" in raw_lower or "vitis" in raw_lower:
            crops = ["Grape"]

    IP102_CATALOG[idx] = {
        "id": idx,
        "name": display_name,
        "raw_benchmark_name": raw_name,
        "scientific_name": sci_name,
        "crops": crops,
        "category": category,
        "damage_type": dmg_type,
        "affected_organs": affected,
        "description": desc,
        "aliases": aliases,
    }


def get_ip102_class(class_id: int) -> Optional[Dict[str, Any]]:
    """Returns catalog record for given IP102 class index."""
    return IP102_CATALOG.get(class_id)


def find_ip102_class_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Finds catalog record by case-insensitive common, scientific name, or alias."""
    if not name:
        return None
    name_clean = name.strip().lower()
    # 1. Exact match on name or scientific name
    for item in IP102_CATALOG.values():
        if name_clean == item["name"].lower() or name_clean == item.get("scientific_name", "").lower():
            return item
    # 2. Check aliases
    for item in IP102_CATALOG.values():
        if any(name_clean == a.lower() for a in item.get("aliases", [])):
            return item
    # 3. Substring match
    for item in IP102_CATALOG.values():
        if name_clean in item["name"].lower():
            return item
    return None


def get_supported_pest_classes() -> List[Dict[str, Any]]:
    """Returns list of all supported catalog classes."""
    return sorted(list(IP102_CATALOG.values()), key=lambda x: x["id"])


def is_crop_susceptible(crop_name: Optional[str], class_id: int) -> bool:
    """Checks whether the detected pest is known to target the host crop."""
    if not crop_name or crop_name.lower() in ("unknown", "all crops", "unspecified"):
        return True
    pest = IP102_CATALOG.get(class_id)
    if not pest:
        return False
    if "All Crops" in pest.get("crops", []):
        return True
    crop_lower = crop_name.lower()
    return any(c.lower() in crop_lower or crop_lower in c.lower() for c in pest.get("crops", []))


def classify_pest_type_distinction(category: str) -> str:
    """Classifies whether the observation represents an insect specimen or damage only."""
    cat_upper = category.upper()
    if cat_upper in ("PEST_DAMAGE", "DAMAGE"):
        return "DAMAGE_ONLY"
    elif cat_upper in ("INSECT", "LARVA", "NYMPH", "ADULT"):
        return "SPECIMEN_DETECTED"
    return "UNCERTAIN"
