"""
plant_search_service.py — Dynamic Plant Species Search Service
--------------------------------------------------------------
Provides real-time plant/crop name suggestions as the user types.

Features:
  - Gemini AI dynamic botanical & crop species search (uses existing GEMINI_API_KEY)
  - Pl@ntNet catalog lookup integration
  - Fast in-memory query caching to minimize API latency
  - ZERO hardcoded crop lists

Allows searching by English common name, Hindi/regional name, or scientific name.
"""

import os
import json
import logging
from typing import List, Dict
from functools import lru_cache

import requests

logger = logging.getLogger(__name__)

# Simple in-memory cache to ensure instant responses for repeated searches
_SEARCH_CACHE: Dict[str, List[Dict]] = {}


def search_gemini_plants(query: str, limit: int = 15) -> List[Dict]:
    """
    Queries Gemini AI to suggest plant and crop species matching the query string.
    Tries stable models in order: gemini-flash-latest, gemini-2.0-flash, gemini-1.5-flash, gemini-2.5-flash.
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.error("google-genai package not installed.")
        return []

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        logger.warning("GEMINI_API_KEY not found.")
        return []

    prompt = f"""You are an agricultural and botanical species search engine.
The user is searching for a plant, crop, fruit, vegetable, spice, or tree and typed: "{query}"

Suggest up to {limit} relevant plant or crop species whose common name, regional name, or scientific name matches "{query}".

Return ONLY valid JSON with this exact structure — no markdown formatting around it:
{{
  "suggestions": [
    {{
      "value": "Common English Name",
      "label": "Common English Name (Scientific Name)",
      "scientific": "Scientific Name"
    }}
  ]
}}

Rules:
- "value" must be the clean, standard common name (e.g. "Mango", "Guava", "Tulasi", "Tomato", "Rice / Paddy")
- "scientific" must be the botanical Latin name (e.g. "Mangifera indica", "Psidium guajava", "Ocimum tenuiflorum")
- "label" combines common and scientific: "Mango (Mangifera indica)"
- Include relevant agricultural crops, fruits, vegetables, field crops, medicinal plants, and plantation species.
- If the user types a regional Indian name (e.g. "bhindi", "tulsi", "karela", "sitaphal"), return the corresponding crop.
"""

    # Try list of models starting with flash models known to work on this key
    candidate_models = [
        os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
        "gemini-flash-latest",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-2.5-flash",
    ]

    client = genai.Client(api_key=api_key)

    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )
            raw = (response.text or "").strip()
            # Clean markdown codeblocks if returned
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            parsed = json.loads(raw)
            suggestions = parsed.get("suggestions", [])
            if suggestions:
                logger.info("Gemini plant search (%s) returned %d results for '%s'", model_name, len(suggestions), query)
                return suggestions[:limit]
        except Exception as e:
            logger.debug("Model %s failed for plant search: %s", model_name, e)
            continue

    logger.warning("All Gemini models failed for query '%s'", query)
    return []


def search_plantnet_species(query: str, limit: int = 15) -> List[Dict]:
    """
    Queries Pl@ntNet species endpoint and filters results locally.
    """
    api_key = os.getenv("PLANT_API_KEY", "").strip()
    if not api_key:
        return []

    url = "https://my-api.plantnet.org/v2/species"
    params = {"api-key": api_key, "lang": "en"}

    try:
        resp = requests.get(url, params=params, timeout=4)
        if resp.status_code != 200:
            return []

        data = resp.json()
        items = data if isinstance(data, list) else data.get("data", [])
        
        q_lower = query.lower()
        results = []
        for item in items:
            sci = item.get("scientificNameWithoutAuthor") or item.get("scientificName", "")
            common_names = item.get("commonNames") or []
            
            # Check match against scientific or common names
            matched_common = next((cn for cn in common_names if q_lower in cn.lower()), None)
            if matched_common or (sci and q_lower in sci.lower()):
                display = matched_common.title() if matched_common else sci
                results.append({
                    "value": display,
                    "label": f"{display} ({sci})" if sci and sci != display else display,
                    "scientific": sci,
                })
        return results[:limit]
    except Exception as e:
        logger.debug("Pl@ntNet search error: %s", e)
        return []


def search_plant_species(query: str, limit: int = 15) -> List[Dict]:
    """
    Public entry point for dynamic plant search.
    Checks memory cache first, then queries Gemini AI & Pl@ntNet API dynamically.
    """
    if not query or len(query.strip()) < 2:
        return []

    cache_key = query.strip().lower()
    if cache_key in _SEARCH_CACHE:
        return _SEARCH_CACHE[cache_key][:limit]

    # 1. Try Gemini AI search (intelligent plant lookup)
    results = search_gemini_plants(query.strip(), limit=limit)

    # 2. Merge with Pl@ntNet matches if Gemini returned few results
    if len(results) < 5:
        pnet_results = search_plantnet_species(query.strip(), limit=limit)
        seen_values = {r["value"].lower() for r in results}
        for pr in pnet_results:
            if pr["value"].lower() not in seen_values:
                results.append(pr)
                seen_values.add(pr["value"].lower())

    if results:
        _SEARCH_CACHE[cache_key] = results

    return results[:limit]
