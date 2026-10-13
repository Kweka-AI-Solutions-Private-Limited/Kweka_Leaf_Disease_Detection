"""
weed_catalog.py — Standardized Taxonomic Catalogs for Benchmark Weed Datasets
-------------------------------------------------------------------------------
Provides canonical metadata for:
  1. DeepWeeds (Alex Olsen et al., 2019):
     - 9 Classes (8 invasive weed species native to Queensland rangelands + 1 Negative class).
     - Task: Single-image classification (ResNet50 / InceptionV3), NO bounding boxes.
     - License: Apache-2.0.

  2. MH-Weed16 (COEP Tech Univ Pune, 2023):
     - 16 Weed species infesting Indian soybean agro-ecosystems (Maharashtra region).
     - Task: Multi-object detection with bounding boxes (YOLO format).
     - License: CC BY 4.0.
"""

from typing import Dict, Any, Optional

DEEPWEEDS_CATALOG: Dict[int, Dict[str, Any]] = {
    0: {
        "name": "Chinee Apple",
        "scientific_name": "Ziziphus mauritiana",
        "botanical_family": "Rhamnaceae",
        "growth_habit": "woody_shrub",
        "category": "INVASIVE_WEED",
        "is_negative": False,
        "description": "Thorny invasive rangeland shrub or small tree forming dense thickets.",
        "regional_context": "Pastoral rangelands, Northern Australia / Tropics",
    },
    1: {
        "name": "Lantana",
        "scientific_name": "Lantana camara",
        "botanical_family": "Verbenaceae",
        "growth_habit": "woody_shrub",
        "category": "NOXIOUS_WEED",
        "is_negative": False,
        "description": "Aggressive, toxic perennial shrub with multicolored flowers disrupting pastures.",
        "regional_context": "Global tropics, pastoral lands, forest borders",
    },
    2: {
        "name": "Parkinsonia",
        "scientific_name": "Parkinsonia aculeata",
        "botanical_family": "Fabaceae",
        "growth_habit": "woody_shrub",
        "category": "WEED_OF_NATIONAL_SIGNIFICANCE",
        "is_negative": False,
        "description": "Spiny legume tree/shrub infesting riverbanks and pastoral grazing lands.",
        "regional_context": "Riparian corridors and semi-arid pastoral plains",
    },
    3: {
        "name": "Parthenium (Congress Grass / Carrot Grass)",
        "scientific_name": "Parthenium hysterophorus",
        "botanical_family": "Asteraceae",
        "growth_habit": "broadleaf",
        "category": "NOXIOUS_WEED",
        "is_negative": False,
        "description": "Prolific allelopathic herb causing severe agricultural yield loss and contact allergies.",
        "regional_context": "Agricultural crops, pastures, and disturbed land worldwide",
    },
    4: {
        "name": "Prickly Acacia",
        "scientific_name": "Vachellia nilotica",
        "botanical_family": "Fabaceae",
        "growth_habit": "woody_tree",
        "category": "WEED_OF_NATIONAL_SIGNIFICANCE",
        "is_negative": False,
        "description": "Thorny invasive tree outcompeting native grasses and forming impenetrable thickets.",
        "regional_context": "Black soil grazing plains",
    },
    5: {
        "name": "Rubber Vine",
        "scientific_name": "Cryptostegia grandiflora",
        "botanical_family": "Apocynaceae",
        "growth_habit": "climbing_vine",
        "category": "WEED_OF_NATIONAL_SIGNIFICANCE",
        "is_negative": False,
        "description": "Vigorous woody climbing vine that smothers riparian tree canopies.",
        "regional_context": "Northern river corridors and tropical woodlands",
    },
    6: {
        "name": "Siam Weed",
        "scientific_name": "Chromolaena odorata",
        "botanical_family": "Asteraceae",
        "growth_habit": "broadleaf_perennial",
        "category": "NOXIOUS_WEED",
        "is_negative": False,
        "description": "Fast-growing perennial shrub forming dense tangles that fuel intense bushfires.",
        "regional_context": "Coastal wet tropics and agricultural margins",
    },
    7: {
        "name": "Snake Weed",
        "scientific_name": "Stachytarpheta jamaicensis",
        "botanical_family": "Verbenaceae",
        "growth_habit": "broadleaf_herb",
        "category": "INVASIVE_WEED",
        "is_negative": False,
        "description": "Herbaceous perennial weed with blue flower spikes that degrades overgrazed pastures.",
        "regional_context": "Subtropical and tropical grazing rangelands",
    },
    8: {
        "name": "Negative (Non-Weed Rangeland / Foliage)",
        "scientific_name": "None",
        "botanical_family": "None",
        "growth_habit": "background",
        "category": "BACKGROUND_NEGATIVE",
        "is_negative": True,
        "description": "Native pasture, ground foliage, or background rangeland devoid of target weed species.",
        "regional_context": "Reference background class in DeepWeeds benchmark",
    },
}

MHWEED16_CATALOG: Dict[int, Dict[str, Any]] = {
    0: {
        "name": "Silver Cockscomb (Safed Murgha)",
        "scientific_name": "Celosia argentea",
        "botanical_family": "Amaranthaceae",
        "growth_habit": "broadleaf",
        "category": "CROP_WEED",
        "is_negative": False,
        "description": "Common annual erect herb infesting kharif soybean and cotton fields in India.",
    },
    1: {
        "name": "Bengal Dayflower (Kena)",
        "scientific_name": "Commelina benghalensis",
        "botanical_family": "Commelinaceae",
        "growth_habit": "creeping_herb",
        "category": "CROP_WEED",
        "is_negative": False,
        "description": "Herbaceous creeping weed producing underground flowers; highly tolerant to glyphosates.",
    },
    2: {
        "name": "Purple Nutsedge (Motha)",
        "scientific_name": "Cyperus rotundus",
        "botanical_family": "Cyperaceae",
        "growth_habit": "sedge",
        "category": "NOXIOUS_WEED",
        "is_negative": False,
        "description": "Extremely persistent perennial tuberous sedge, regarded as one of the world's worst weeds.",
    },
    3: {
        "name": "Parthenium (Congress Grass / Gajar Ghas)",
        "scientific_name": "Parthenium hysterophorus",
        "botanical_family": "Asteraceae",
        "growth_habit": "broadleaf",
        "category": "NOXIOUS_WEED",
        "is_negative": False,
        "description": "Invasive allelopathic weed causing major yield decline in soybean crops.",
    },
    4: {
        "name": "Asthma Plant (Dudhi)",
        "scientific_name": "Euphorbia hirta",
        "botanical_family": "Euphorbiaceae",
        "growth_habit": "broadleaf",
        "category": "CROP_WEED",
        "is_negative": False,
        "description": "Hairy annual herb with milky sap occurring extensively in agricultural fields.",
    },
    5: {
        "name": "False Amaranth (Kundra)",
        "scientific_name": "Digera arvensis",
        "botanical_family": "Amaranthaceae",
        "growth_habit": "broadleaf",
        "category": "CROP_WEED",
        "is_negative": False,
        "description": "Annual erect herb common in rainfed kharif crops in Maharashtra.",
    },
    6: {
        "name": "Egyptian Crowfoot Grass",
        "scientific_name": "Dactyloctenium aegyptium",
        "botanical_family": "Poaceae",
        "growth_habit": "grass",
        "category": "CROP_WEED",
        "is_negative": False,
        "description": "Spreading annual grass with finger-like digitated spikes competing with young seedlings.",
    },
    7: {
        "name": "Jungle Rice (Sawa Grass)",
        "scientific_name": "Echinochloa colona",
        "botanical_family": "Poaceae",
        "growth_habit": "grass",
        "category": "CROP_WEED",
        "is_negative": False,
        "description": "Major annual grass mimicking cereal crops, common in wet soils and crop furrows.",
    },
    8: {
        "name": "Gale of the Wind (Bhuiamla)",
        "scientific_name": "Phyllanthus niruri",
        "botanical_family": "Phyllanthaceae",
        "growth_habit": "broadleaf",
        "category": "CROP_WEED",
        "is_negative": False,
        "description": "Small annual weed with pinnate leaflets competing for soil moisture in crop rows.",
    },
    9: {
        "name": "Indian Acalypha (Khokli)",
        "scientific_name": "Acalypha indica",
        "botanical_family": "Euphorbiaceae",
        "growth_habit": "broadleaf",
        "category": "CROP_WEED",
        "is_negative": False,
        "description": "Erect annual herb growing in shady or moist borders of agricultural fields.",
    },
    10: {
        "name": "Slender Amaranth (Chaulai)",
        "scientific_name": "Amaranthus viridis",
        "botanical_family": "Amaranthaceae",
        "growth_habit": "broadleaf",
        "category": "CROP_WEED",
        "is_negative": False,
        "description": "Fast-growing annual broadleaf herb with dense seed production.",
    },
    11: {
        "name": "Bermuda Grass (Doob Ghas / Hariali)",
        "scientific_name": "Cynodon dactylon",
        "botanical_family": "Poaceae",
        "growth_habit": "stoloniferous_grass",
        "category": "PERENNIAL_WEED",
        "is_negative": False,
        "description": "Deep-rooted creeping perennial grass that forms dense mats in agricultural plots.",
    },
    12: {
        "name": "Common Purslane (Ghol)",
        "scientific_name": "Portulaca oleracea",
        "botanical_family": "Portulacaceae",
        "growth_habit": "succulent_broadleaf",
        "category": "CROP_WEED",
        "is_negative": False,
        "description": "Prostrate succulent annual weed capable of re-rooting from stem fragments.",
    },
    13: {
        "name": "Coatbuttons (Dagadi Pala)",
        "scientific_name": "Tridax procumbens",
        "botanical_family": "Asteraceae",
        "growth_habit": "broadleaf",
        "category": "CROP_WEED",
        "is_negative": False,
        "description": "Sprawling perennial daisy herb with dandelion-like seeds infesting bunds and field edges.",
    },
    14: {
        "name": "Rough Cocklebur (Gokhru / Bhurat)",
        "scientific_name": "Xanthium strumarium",
        "botanical_family": "Asteraceae",
        "growth_habit": "broadleaf",
        "category": "NOXIOUS_WEED",
        "is_negative": False,
        "description": "Coarse annual herb producing spiny burrs that cling to clothing and livestock.",
    },
    15: {
        "name": "Field Bindweed (Haranpadi)",
        "scientific_name": "Convolvulus arvensis",
        "botanical_family": "Convolvulaceae",
        "growth_habit": "climbing_vine",
        "category": "NOXIOUS_WEED",
        "is_negative": False,
        "description": "Deeply rooted perennial creeping morning-glory vine that twines around crop stems.",
    },
}


def get_deepweeds_class(class_id: int) -> Optional[Dict[str, Any]]:
    """Fetches DeepWeeds class metadata by integer index (0-8)."""
    return DEEPWEEDS_CATALOG.get(class_id)


def get_mhweed16_class(class_id: int) -> Optional[Dict[str, Any]]:
    """Fetches MH-Weed16 class metadata by integer index (0-15)."""
    return MHWEED16_CATALOG.get(class_id)


AGRICULTURAL_YOLO_WEEDS_CATALOG: Dict[str, Dict[str, Any]] = {
    "dandelion": {
        "name": "Common Dandelion",
        "scientific_name": "Taraxacum officinale",
        "botanical_family": "Asteraceae",
        "growth_habit": "taproot_broadleaf",
        "category": "AGRICULTURAL_WEED",
        "is_negative": False,
        "description": "Perennial broadleaf weed with deep taproot and wind-dispersed seeds.",
    },
    "cow parsley": {
        "name": "Cow Parsley (Wild Chervil)",
        "scientific_name": "Anthriscus sylvestris",
        "botanical_family": "Apiaceae",
        "growth_habit": "herbaceous_biennial",
        "category": "AGRICULTURAL_WEED",
        "is_negative": False,
        "description": "Fast-spreading biennial herb that shadows and chokes out young crop and pasture seedlings.",
    },
    "dock": {
        "name": "Broad-leaved Dock",
        "scientific_name": "Rumex obtusifolius",
        "botanical_family": "Polygonaceae",
        "growth_habit": "perennial_broadleaf",
        "category": "AGRICULTURAL_WEED",
        "is_negative": False,
        "description": "Persistent taprooted perennial weed common in agricultural pastures and cultivated borders.",
    },
    "nettle": {
        "name": "Stinging Nettle",
        "scientific_name": "Urtica dioica",
        "botanical_family": "Urticaceae",
        "growth_habit": "perennial_broadleaf",
        "category": "AGRICULTURAL_WEED",
        "is_negative": False,
        "description": "Vigorous perennial weed with stinging trichomes, competing fiercely for soil nitrogen.",
    },
    "thistle": {
        "name": "Creeping Thistle / Field Thistle",
        "scientific_name": "Cirsium arvense",
        "botanical_family": "Asteraceae",
        "growth_habit": "rhizomatous_broadleaf",
        "category": "NOXIOUS_WEED",
        "is_negative": False,
        "description": "Aggressive spiny perennial weed with deep spreading rhizomes causing substantial crop yield loss.",
    },
    "weed": {
        "name": "Unspecified Agricultural Weed",
        "scientific_name": None,
        "botanical_family": None,
        "growth_habit": "broadleaf",
        "category": "AGRICULTURAL_WEED",
        "is_negative": False,
        "description": "Detected weed specimen in crop foliage.",
    },
}


def resolve_weed_class(class_id: int, raw_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Resolves canonical weed metadata by checking:
      1. Model raw class name in AGRICULTURAL_YOLO_WEEDS_CATALOG
      2. MH-Weed16 class ID
      3. DeepWeeds class ID
      4. Fallback generic representation
    """
    if raw_name:
        clean_key = raw_name.strip().lower()
        if clean_key in AGRICULTURAL_YOLO_WEEDS_CATALOG:
            return AGRICULTURAL_YOLO_WEEDS_CATALOG[clean_key]
        for k, v in AGRICULTURAL_YOLO_WEEDS_CATALOG.items():
            if k in clean_key:
                return v

    meta = get_mhweed16_class(class_id)
    if meta:
        return meta

    meta = get_deepweeds_class(class_id)
    if meta:
        return meta

    fallback_name = raw_name or f"Weed Class {class_id}"
    return {
        "name": fallback_name,
        "scientific_name": None,
        "botanical_family": None,
        "growth_habit": "weed",
        "category": "CROP_WEED",
        "is_negative": False,
        "description": "Detected weed instance.",
    }

