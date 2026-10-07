"""
plant_identifier.py — Crop/Plant Identification Service (Phase 1)
------------------------------------------------------------------
Identifies crop/plant species from validated images or accepts explicit
user-selected crop override.
"""

from typing import Optional, List, Dict
from schemas.leaf_disease import CropIdentificationResult


# ─── Master plant/crop database ───────────────────────────────────────────────
# Maps lowercase search keywords → canonical display name used across the pipeline.
# Organised by category for the /plants API endpoint.

PLANT_CATALOG: List[Dict] = [
    # ── Fruits ────────────────────────────────────────────────────────────────
    {"value": "Mango",              "label": "Mango",                                  "category": "Fruits"},
    {"value": "Guava",              "label": "Guava",                                  "category": "Fruits"},
    {"value": "Banana",             "label": "Banana",                                 "category": "Fruits"},
    {"value": "Apple",              "label": "Apple",                                  "category": "Fruits"},
    {"value": "Pear",               "label": "Pear (Pyrus)",                           "category": "Fruits"},
    {"value": "Grape",              "label": "Grape",                                  "category": "Fruits"},
    {"value": "Papaya",             "label": "Papaya",                                 "category": "Fruits"},
    {"value": "Pomegranate",        "label": "Pomegranate",                            "category": "Fruits"},
    {"value": "Lemon",              "label": "Lemon / Lime",                           "category": "Fruits"},
    {"value": "Orange",             "label": "Orange",                                 "category": "Fruits"},
    {"value": "Citrus",             "label": "Citrus (General)",                       "category": "Fruits"},
    {"value": "Watermelon",         "label": "Watermelon",                             "category": "Fruits"},
    {"value": "Strawberry",         "label": "Strawberry",                             "category": "Fruits"},
    {"value": "Avocado",            "label": "Avocado",                                "category": "Fruits"},
    {"value": "Coconut",            "label": "Coconut",                                "category": "Fruits"},
    {"value": "Jackfruit",          "label": "Jackfruit",                              "category": "Fruits"},
    {"value": "Litchi",             "label": "Litchi / Lychee",                        "category": "Fruits"},
    {"value": "Sapota",             "label": "Sapota / Chikoo",                        "category": "Fruits"},
    {"value": "Custard Apple",      "label": "Custard Apple / Sitaphal",               "category": "Fruits"},
    {"value": "Mulberry",           "label": "Mulberry",                               "category": "Fruits"},
    {"value": "Fig",                "label": "Fig",                                    "category": "Fruits"},
    {"value": "Passion Fruit",      "label": "Passion Fruit",                          "category": "Fruits"},
    {"value": "Dragon Fruit",       "label": "Dragon Fruit",                           "category": "Fruits"},
    {"value": "Kiwi",               "label": "Kiwi",                                   "category": "Fruits"},
    {"value": "Cherry",             "label": "Cherry",                                 "category": "Fruits"},
    {"value": "Peach",              "label": "Peach",                                  "category": "Fruits"},
    {"value": "Plum",               "label": "Plum",                                   "category": "Fruits"},
    {"value": "Apricot",            "label": "Apricot",                                "category": "Fruits"},
    {"value": "Blueberry",          "label": "Blueberry",                              "category": "Fruits"},
    # ── Vegetables ────────────────────────────────────────────────────────────
    {"value": "Tomato",             "label": "Tomato",                                 "category": "Vegetables"},
    {"value": "Potato",             "label": "Potato",                                 "category": "Vegetables"},
    {"value": "Chilli / Pepper",    "label": "Chilli / Pepper",                        "category": "Vegetables"},
    {"value": "Cucurbits",          "label": "Cucurbits (Cucumber / Melon / Squash / Pumpkin)", "category": "Vegetables"},
    {"value": "Brinjal / Eggplant", "label": "Brinjal / Eggplant",                    "category": "Vegetables"},
    {"value": "Onion",              "label": "Onion",                                  "category": "Vegetables"},
    {"value": "Garlic",             "label": "Garlic",                                 "category": "Vegetables"},
    {"value": "Okra / Bhindi",      "label": "Okra / Bhindi",                          "category": "Vegetables"},
    {"value": "Cabbage",            "label": "Cabbage",                                "category": "Vegetables"},
    {"value": "Cauliflower",        "label": "Cauliflower",                            "category": "Vegetables"},
    {"value": "Spinach",            "label": "Spinach",                                "category": "Vegetables"},
    {"value": "Carrot",             "label": "Carrot",                                 "category": "Vegetables"},
    {"value": "Ginger",             "label": "Ginger",                                 "category": "Vegetables"},
    {"value": "Turmeric",           "label": "Turmeric",                               "category": "Vegetables"},
    {"value": "Peas",               "label": "Peas",                                   "category": "Vegetables"},
    {"value": "Beans",              "label": "Beans / French Beans",                   "category": "Vegetables"},
    {"value": "Bitter Gourd",       "label": "Bitter Gourd / Karela",                  "category": "Vegetables"},
    {"value": "Bottle Gourd",       "label": "Bottle Gourd / Lauki",                   "category": "Vegetables"},
    {"value": "Ridge Gourd",        "label": "Ridge Gourd / Turai",                    "category": "Vegetables"},
    {"value": "Tulasi",             "label": "Tulasi / Holy Basil",                    "category": "Vegetables"},
    {"value": "Moringa",            "label": "Moringa / Drumstick",                    "category": "Vegetables"},
    {"value": "Curry Leaf",         "label": "Curry Leaf",                             "category": "Vegetables"},
    # ── Field Crops ───────────────────────────────────────────────────────────
    {"value": "Rice / Paddy",          "label": "Rice / Paddy",                        "category": "Field Crops"},
    {"value": "Wheat",                 "label": "Wheat",                               "category": "Field Crops"},
    {"value": "Maize / Corn",          "label": "Maize / Corn",                        "category": "Field Crops"},
    {"value": "Sugarcane",             "label": "Sugarcane",                           "category": "Field Crops"},
    {"value": "Cotton",                "label": "Cotton",                              "category": "Field Crops"},
    {"value": "Groundnut / Peanut",    "label": "Groundnut / Peanut",                  "category": "Field Crops"},
    {"value": "Soybean",               "label": "Soybean",                             "category": "Field Crops"},
    {"value": "Sunflower",             "label": "Sunflower",                           "category": "Field Crops"},
    {"value": "Mustard / Rapeseed",    "label": "Mustard / Rapeseed",                  "category": "Field Crops"},
    {"value": "Sorghum / Jowar",       "label": "Sorghum / Jowar",                     "category": "Field Crops"},
    {"value": "Pearl Millet / Bajra",  "label": "Pearl Millet / Bajra",               "category": "Field Crops"},
    {"value": "Finger Millet / Ragi",  "label": "Finger Millet / Ragi",               "category": "Field Crops"},
    {"value": "Chickpea / Gram",       "label": "Chickpea / Gram",                     "category": "Field Crops"},
    {"value": "Lentil / Masoor",       "label": "Lentil / Masoor",                     "category": "Field Crops"},
    {"value": "Pigeon Pea / Arhar",    "label": "Pigeon Pea / Arhar",                  "category": "Field Crops"},
    {"value": "Black Gram / Urad",     "label": "Black Gram / Urad",                   "category": "Field Crops"},
    {"value": "Green Gram / Moong",    "label": "Green Gram / Moong",                  "category": "Field Crops"},
    {"value": "Sesame / Til",          "label": "Sesame / Til",                        "category": "Field Crops"},
    {"value": "Jute",                  "label": "Jute",                                "category": "Field Crops"},
    {"value": "Tobacco",               "label": "Tobacco",                             "category": "Field Crops"},
    {"value": "Flax / Linseed",        "label": "Flax / Linseed",                      "category": "Field Crops"},
    {"value": "Castor",                "label": "Castor",                              "category": "Field Crops"},
    # ── Plantation & Spices ───────────────────────────────────────────────────
    {"value": "Tea",                "label": "Tea",                                    "category": "Plantation"},
    {"value": "Coffee",             "label": "Coffee",                                 "category": "Plantation"},
    {"value": "Rubber",             "label": "Rubber",                                 "category": "Plantation"},
    {"value": "Arecanut",           "label": "Arecanut / Betelnut",                    "category": "Plantation"},
    {"value": "Cardamom",           "label": "Cardamom",                               "category": "Plantation"},
    {"value": "Pepper",             "label": "Black Pepper",                           "category": "Plantation"},
    {"value": "Cashew",             "label": "Cashew",                                 "category": "Plantation"},
    {"value": "Tamarind",           "label": "Tamarind",                               "category": "Plantation"},
    {"value": "Neem",               "label": "Neem",                                   "category": "Plantation"},
    {"value": "Eucalyptus",         "label": "Eucalyptus",                             "category": "Plantation"},
    {"value": "Teak",               "label": "Teak",                                   "category": "Plantation"},
    {"value": "Cocoa",              "label": "Cocoa",                                  "category": "Plantation"},
    {"value": "Vanilla",            "label": "Vanilla",                                "category": "Plantation"},
    {"value": "Clove",              "label": "Clove",                                  "category": "Plantation"},
    {"value": "Nutmeg",             "label": "Nutmeg",                                 "category": "Plantation"},
    {"value": "Cinnamon",           "label": "Cinnamon",                               "category": "Plantation"},
    {"value": "Bamboo",             "label": "Bamboo",                                 "category": "Plantation"},
]

# Flat keyword → canonical display name lookup (used internally for auto-detection)
KNOWN_CROPS: Dict[str, str] = {}
for _p in PLANT_CATALOG:
    _val   = _p["value"].lower()
    _label = _p["value"]
    KNOWN_CROPS[_val] = _label
    # Also index individual words for partial matching (e.g. "paddy" → "Rice / Paddy")
    for _word in _val.split():
        if len(_word) > 3:
            KNOWN_CROPS.setdefault(_word.strip("/."), _label)

# Extra common aliases not covered by splitting
_ALIASES = {
    "cucumber": "Cucurbits", "melon": "Cucurbits", "squash": "Cucurbits",
    "pumpkin": "Cucurbits", "gourd": "Cucurbits", "cucurbit": "Cucurbits",
    "chilli": "Chilli / Pepper", "chili": "Chilli / Pepper",
    "corn": "Maize / Corn", "maize": "Maize / Corn",
    "paddy": "Rice / Paddy", "rice": "Rice / Paddy",
    "groundnut": "Groundnut / Peanut", "peanut": "Groundnut / Peanut",
    "brinjal": "Brinjal / Eggplant", "eggplant": "Brinjal / Eggplant",
    "bhindi": "Okra / Bhindi", "okra": "Okra / Bhindi",
    "karela": "Bitter Gourd", "bittergourd": "Bitter Gourd",
    "lauki": "Bottle Gourd", "bottlegourd": "Bottle Gourd",
    "turai": "Ridge Gourd",
    "jowar": "Sorghum / Jowar", "sorghum": "Sorghum / Jowar",
    "bajra": "Pearl Millet / Bajra",
    "ragi": "Finger Millet / Ragi",
    "gram": "Chickpea / Gram", "chickpea": "Chickpea / Gram",
    "masoor": "Lentil / Masoor", "lentil": "Lentil / Masoor",
    "arhar": "Pigeon Pea / Arhar", "tur": "Pigeon Pea / Arhar",
    "urad": "Black Gram / Urad",
    "moong": "Green Gram / Moong",
    "til": "Sesame / Til", "sesame": "Sesame / Til",
    "mustard": "Mustard / Rapeseed", "rapeseed": "Mustard / Rapeseed",
    "lemon": "Lemon", "lime": "Lemon",
    "litchi": "Litchi", "lychee": "Litchi",
    "chikoo": "Sapota",
    "sitaphal": "Custard Apple",
    "holy basil": "Tulasi", "tulsi": "Tulasi",
    "drumstick": "Moringa",
    "arecanut": "Arecanut", "betelnut": "Arecanut",
    "black pepper": "Pepper",
    "cocoa": "Cocoa",
}
KNOWN_CROPS.update(_ALIASES)


def get_all_plant_species() -> List[Dict]:
    """Returns the full plant catalog for the frontend species selector."""
    return PLANT_CATALOG


def identify_crop(
    selected_crop: Optional[str] = None,
    valid_filenames: Optional[List[str]] = None
) -> CropIdentificationResult:
    """
    Identifies crop/plant. If user selected a crop explicitly, honors user override.
    Otherwise attempts automatic crop detection (or returns UNCERTAIN if non-deterministic).
    """
    # 1. User Override Check
    if selected_crop and selected_crop.strip():
        clean_selected = selected_crop.strip().lower()
        matched_display_name = KNOWN_CROPS.get(clean_selected, selected_crop.strip().title())
        return CropIdentificationResult(
            crop_name=matched_display_name,
            confidence=1.0,
            source="user_selected",
            status="USER_SPECIFIED",
            evidence_note=f"Crop specified as '{matched_display_name}' by user selection."
        )

    # 2. Defer to AI Visual Crop Identification (Pl@ntNet / Gemini VLM)
    # When user does not explicitly select a crop, return UNCERTAIN to invoke Gemini VLM visual morphology analysis.
    return CropIdentificationResult(
        crop_name="Unknown",
        confidence=0.0,
        source="automatic",
        status="UNCERTAIN",
        evidence_note="Crop identification deferred to AI visual leaf morphology analysis."
    )

