"""
leaf_advisory_service.py — Service layer for Leaf Advisory with Gemini & NACL Catalog
---------------------------------------------------------------------------------------
Handles:
  1. Historical diagnosis query across Leaf Scanner & Leaf Diagnosis runs
  2. NACL Agrochemical Product retrieval for identified crop, disease, and pest
  3. Context-aware agronomist advisory synthesis using Gemini VLM/LLM
     (accounting for optional Geolocation & Season)
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pymongo.database import Database

from schemas.leaf_advisory import (
    AdvisoryHistoricalDiagnosisItem,
    LeafAdvisoryRequest,
    SeasonalRiskAssessment,
    LeafAdvisoryResponse
)
from schemas.nacl_catalog import NACLProductRecommendation
from db.nacl_product_db import query_nacl_products, get_db

logger = logging.getLogger(__name__)

INSPECTIONS_COLLECTION = "ldd_inspections"


def _get_gemini_client():
    """Initializes and returns Gemini client if API key is available."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.warning(f"Could not initialize Gemini client: {e}")
        return None


class LeafAdvisoryService:
    """Service orchestrating historical diagnostic lookups and agronomic advisory generation."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db if db is not None else get_db()

    def get_historical_diagnoses(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[AdvisoryHistoricalDiagnosisItem]:
        """
        Retrieves recent historical diagnoses from 'ldd_inspections' MongoDB collection.
        Returns normalized diagnostic records suitable for advisory selection.
        """
        query: Dict[str, Any] = {}
        if user_id:
            query["user_id"] = user_id

        cursor = self.db[INSPECTIONS_COLLECTION].find(query).sort("created_at", -1).limit(limit)

        items: List[AdvisoryHistoricalDiagnosisItem] = []
        for doc in cursor:
            try:
                analysis_id = str(doc.get("analysis_id") or doc.get("_id") or "")
                created_at = doc.get("created_at") or doc.get("timestamp")
                if isinstance(created_at, datetime):
                    timestamp_str = created_at.isoformat()
                else:
                    timestamp_str = str(created_at or datetime.now(timezone.utc).isoformat())

                source = doc.get("source") or ("LEAF_DIAGNOSIS" if doc.get("cross_validation") else "LEAF_SCANNER")

                # Extract Crop
                crop_doc = doc.get("crop") or {}
                crop_name = crop_doc.get("crop_name") or "Unknown Crop"

                # Extract Disease
                disease_doc = doc.get("disease") or {}
                disease_name = disease_doc.get("disease_name")
                if disease_name and disease_name.lower() in ("no pathology detected", "none", "unknown"):
                    disease_name = None

                # Extract Pest
                pest_doc = doc.get("pest") or {}
                pest_name = pest_doc.get("primary_pest")
                if pest_name and pest_name.lower() in ("none", "no pest detected", "unknown pest", "no_pest_detected"):
                    pest_name = None

                # Confidence & Status
                status = doc.get("status") or "SUCCESS"
                confidence = None
                if disease_doc.get("confidence") is not None:
                    confidence = float(disease_doc["confidence"])
                elif crop_doc.get("confidence") is not None:
                    confidence = float(crop_doc["confidence"])

                summary_parts = []
                if crop_name and crop_name != "Unknown Crop":
                    summary_parts.append(f"Crop: {crop_name}")
                if disease_name:
                    summary_parts.append(f"Disease: {disease_name}")
                if pest_name:
                    summary_parts.append(f"Pest: {pest_name}")
                summary = " • ".join(summary_parts) if summary_parts else f"Analysis {analysis_id[:8]}"
                image_url = doc.get("image_url") or doc.get("thumbnail")

                items.append(
                    AdvisoryHistoricalDiagnosisItem(
                        analysis_id=analysis_id,
                        source=source,
                        timestamp=timestamp_str,
                        crop_name=crop_name,
                        disease_name=disease_name,
                        pest_name=pest_name,
                        status=status,
                        confidence=confidence,
                        summary=summary,
                        image_url=image_url,
                    )
                )
            except Exception as ex:
                logger.warning(f"Error parsing historical doc: {ex}")
                continue

        return items

    def generate_advisory(self, request: LeafAdvisoryRequest) -> LeafAdvisoryResponse:
        """
        Generates tailored agronomist advice, seasonal risks, and verified NACL product remedies.
        Geolocation and season are optional.
        """
        advisory_id = f"adv_{uuid.uuid4().hex[:12]}"
        timestamp_str = datetime.now(timezone.utc).isoformat()

        crop_clean = request.crop_name.strip()
        disease_clean = (request.disease_name or "").strip()
        pest_clean = (request.pest_name or "").strip()
        geo_clean = (request.geolocation or "").strip() if request.geolocation else None
        season_clean = (request.season or "").strip() if request.season else None

        # 1. Retrieve matching NACL Agrochemical Products
        matched_recommendations = self._retrieve_nacl_products(
            crop_name=crop_clean,
            disease_name=disease_clean,
            pest_name=pest_clean
        )

        # 2. Synthesize Gemini Agronomist Advisory with Regional & Seasonal Awareness
        gemini_result = self._synthesize_gemini_advisory(
            crop_name=crop_clean,
            disease_name=disease_clean,
            pest_name=pest_clean,
            geolocation=geo_clean,
            season=season_clean,
            recommendations=matched_recommendations
        )

        seasonal_risk = SeasonalRiskAssessment(
            season_name=season_clean or "General / All Season",
            geolocation_name=geo_clean or "General Agricultural Region",
            climate_factors=gemini_result["climate_factors"],
            disease_pressure_level=gemini_result["disease_pressure_level"],
            weather_spray_window_advice=gemini_result["weather_spray_window_advice"],
        )

        image_url = request.image_url
        if not image_url and request.analysis_id:
            try:
                hist_doc = self.db[INSPECTIONS_COLLECTION].find_one({"analysis_id": request.analysis_id})
                if hist_doc:
                    image_url = hist_doc.get("image_url") or hist_doc.get("thumbnail")
            except Exception:
                pass

        return LeafAdvisoryResponse(
            advisory_id=advisory_id,
            timestamp=timestamp_str,
            crop_name=crop_clean,
            disease_name=disease_clean or None,
            pest_name=pest_clean or None,
            geolocation=geo_clean,
            season=season_clean,
            seasonal_risk=seasonal_risk,
            nacl_products=matched_recommendations,
            ai_advisory_summary=gemini_result["ai_advisory_summary"],
            cultural_remedies=gemini_result["cultural_remedies"],
            chemical_management=gemini_result["chemical_management"],
            image_url=image_url,
        )

    def _retrieve_nacl_products(
        self,
        crop_name: str,
        disease_name: str,
        pest_name: str
    ) -> List[NACLProductRecommendation]:
        """Queries and normalizes matching NACL catalog products for the crop, disease, and pest."""
        recs: List[NACLProductRecommendation] = []
        seen_ids = set()

        # Step 1: Query fungicides matching disease/crop
        if disease_name:
            disease_prods = query_nacl_products(crop_name=crop_name, disease_name=disease_name, category="Fungicide", db=self.db)
            for p in disease_prods:
                p_id = p.get("product_id")
                if p_id and p_id not in seen_ids:
                    seen_ids.add(p_id)
                    app_dosage = "Refer to product label"
                    if p.get("crop_applications"):
                        for app in p["crop_applications"]:
                            if app.get("dosage"):
                                app_dosage = app["dosage"]
                                break
                    recs.append(
                        NACLProductRecommendation(
                            product_id=p_id,
                            product_name=p.get("product_name", p_id.title()),
                            category="Fungicide",
                            product_url=p.get("product_url", "https://naclind.com/products/"),
                            active_ingredient=p.get("active_ingredient"),
                            match_type="VERIFIED_DISEASE_MATCH",
                            verification_status="VERIFIED_CROP_TARGET_MATCH",
                            dosage_verified=True,
                            recommended_dosage=app_dosage,
                            match_rationale=f"Registered NACL fungicide for {disease_name} on {crop_name}.",
                            pack_sizes=p.get("pack_sizes", []),
                            frac_group=p.get("frac_group")
                        )
                    )

        # Step 2: Query insecticides matching pest/crop
        if pest_name:
            pest_prods = query_nacl_products(crop_name=crop_name, disease_name=pest_name, category="Insecticide", db=self.db)
            for p in pest_prods:
                p_id = p.get("product_id")
                if p_id and p_id not in seen_ids:
                    seen_ids.add(p_id)
                    app_dosage = "Refer to product label"
                    if p.get("crop_applications"):
                        for app in p["crop_applications"]:
                            if app.get("dosage"):
                                app_dosage = app["dosage"]
                                break
                    recs.append(
                        NACLProductRecommendation(
                            product_id=p_id,
                            product_name=p.get("product_name", p_id.title()),
                            category="Insecticide",
                            product_url=p.get("product_url", "https://naclind.com/products/"),
                            active_ingredient=p.get("active_ingredient"),
                            match_type="VERIFIED_PEST_MATCH",
                            verification_status="VERIFIED_CROP_TARGET_MATCH",
                            dosage_verified=True,
                            recommended_dosage=app_dosage,
                            match_rationale=f"Registered NACL insecticide for {pest_name} management on {crop_name}.",
                            pack_sizes=p.get("pack_sizes", []),
                            frac_group=p.get("frac_group")
                        )
                    )

        # Step 3: Broad category fallback if fewer than 2 products found
        if len(recs) < 3:
            target_cat = "Insecticide" if pest_name and not disease_name else "Fungicide"
            fallback_prods = query_nacl_products(category=target_cat, db=self.db)
            for p in fallback_prods:
                p_id = p.get("product_id")
                if p_id and p_id not in seen_ids:
                    seen_ids.add(p_id)
                    recs.append(
                        NACLProductRecommendation(
                            product_id=p_id,
                            product_name=p.get("product_name", p_id.title()),
                            category=p.get("category", target_cat),
                            product_url=p.get("product_url", "https://naclind.com/products/"),
                            active_ingredient=p.get("active_ingredient"),
                            match_type="PRELIMINARY_ADVISORY_MATCH",
                            verification_status="PRELIMINARY_ADVISORY_MATCH",
                            dosage_verified=False,
                            recommended_dosage=p.get("crop_applications", [{}])[0].get("dosage", "Refer to current product label"),
                            match_rationale=f"NACL {target_cat} formulation for crop protection.",
                            pack_sizes=p.get("pack_sizes", []),
                            frac_group=p.get("frac_group")
                        )
                    )
                if len(recs) >= 4:
                    break

        return recs[:4]

    def _synthesize_gemini_advisory(
        self,
        crop_name: str,
        disease_name: str,
        pest_name: str,
        geolocation: Optional[str],
        season: Optional[str],
        recommendations: List[NACLProductRecommendation]
    ) -> Dict[str, Any]:
        """Calls Gemini with crop, diagnosis, optional geolocation, and season to produce tailored advice."""
        client = _get_gemini_client()

        # Build verified product descriptions
        products_text = ""
        for r in recommendations:
            dosage = r.recommended_dosage or "Refer to product label"
            frac = f" (FRAC/IRAC: {r.frac_group})" if r.frac_group else ""
            products_text += f"- {r.product_name} ({r.category}): Active ingredient '{r.active_ingredient}'{frac}. Dosage: {dosage}.\n"

        geo_desc = geolocation if geolocation else "General agricultural zone (unspecified region)"
        season_desc = season if season else "Standard growing season (unspecified climate)"

        # Fallback dictionary if Gemini is unavailable
        fallback_data = {
            "climate_factors": (
                f"Under {season_desc} in {geo_desc}, ambient temperature and canopy microclimate strongly influence "
                f"foliar infection and insect pest emergence. Maintain vigilance during prolonged dew or wet periods."
            ),
            "disease_pressure_level": "MODERATE" if (disease_name or pest_name) else "LOW",
            "weather_spray_window_advice": (
                "Apply foliar treatments during calm early morning or late afternoon hours. "
                "Ensure minimum 2-3 rain-free hours following application for optimal chemical absorption."
            ),
            "ai_advisory_summary": (
                f"For the protection of {crop_name} affected by {disease_name or pest_name or 'foliar stress'}, "
                f"an integrated crop management approach combining cultural sanitation and targeted NACL chemistries is recommended. "
                f"Ensure even canopy coverage and follow recommended label dosages."
            ),
            "cultural_remedies": [
                f"Prune and destroy heavily infested lower leaves to reduce pathogen inoculum.",
                f"Optimize plant spacing and avoid excessive overhead sprinkler irrigation to keep canopy dry.",
                f"Maintain field sanitation and eliminate alternate weed hosts around perimeter boundaries.",
                f"Ensure balanced nitrogen fertilization; avoid excessive nitrogen that promotes lush, susceptible foliage."
            ],
            "chemical_management": [
                f"Apply verified NACL formulations targeting early symptom onset.",
                f"Rotate products with different FRAC/IRAC modes of action to prevent resistance development.",
                f"Use flat-fan nozzles at 30-40 PSI pressure for uniform foliar droplet deposition."
            ]
        }

        if not client:
            return fallback_data

        models_to_try = [
            os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]

        prompt = f"""You are a senior agricultural agronomist and plant pathologist specializing in Indian and global crop protection.
A farmer has requested expert advisory and remedies for their crop.

DIAGNOSTIC DETAILS:
- Crop: {crop_name}
- Diagnosed Disease / Pathology: {disease_name or 'None identified'}
- Diagnosed Insect Pest: {pest_name or 'None identified'}
- Geolocation / Region: {geo_desc}
- Season: {season_desc}

VERIFIED NACL AGROCHEMICAL CATALOG PRODUCTS AVAILABLE:
{products_text if products_text else 'No direct registered products in current catalog index.'}

INSTRUCTIONS:
Synthesize a comprehensive, practical agronomic advisory tailored to the crop condition, regional context, and season (or general best practices if region/season are unspecified).
Respond ONLY with a valid JSON object matching this schema:
{{
  "climate_factors": "2-3 sentences explaining how this specific season and region (or general humidity/temperature) impact the life cycle, spore propagation, or pest feeding pressure.",
  "disease_pressure_level": "HIGH or MODERATE or LOW",
  "weather_spray_window_advice": "Specific recommendation on optimal spraying time of day, wind speed, rain avoidance, or temperature safety window for this season.",
  "ai_advisory_summary": "2-3 paragraphs providing an agronomist advisory explaining what the farmer is facing, how the recommended NACL active ingredients resolve it, and what immediate action is required.",
  "cultural_remedies": [
    "Practical cultural/agronomic remedy 1 (drainage, spacing, sanitation)",
    "Practical cultural/agronomic remedy 2",
    "Practical cultural/agronomic remedy 3",
    "Practical cultural/agronomic remedy 4"
  ],
  "chemical_management": [
    "Specific instruction on applying the verified NACL chemistries",
    "Resistance management guidance (FRAC/IRAC rotation)",
    "Spraying safety and application equipment tips"
  ]
}}
Do not invent unverified brands outside of the provided NACL products.
"""

        for m in models_to_try:
            try:
                res = client.models.generate_content(
                    model=m,
                    contents=[prompt],
                    config={"response_mime_type": "application/json"}
                )
                if res and res.text:
                    parsed = json.loads(res.text)
                    if isinstance(parsed, dict) and "ai_advisory_summary" in parsed:
                        return {
                            "climate_factors": parsed.get("climate_factors", fallback_data["climate_factors"]),
                            "disease_pressure_level": parsed.get("disease_pressure_level", "MODERATE"),
                            "weather_spray_window_advice": parsed.get("weather_spray_window_advice", fallback_data["weather_spray_window_advice"]),
                            "ai_advisory_summary": parsed.get("ai_advisory_summary", fallback_data["ai_advisory_summary"]),
                            "cultural_remedies": parsed.get("cultural_remedies", fallback_data["cultural_remedies"]),
                            "chemical_management": parsed.get("chemical_management", fallback_data["chemical_management"]),
                        }
            except Exception as ex:
                logger.warning(f"Gemini advisory generation with model {m} failed: {ex}")
                continue

        return fallback_data
