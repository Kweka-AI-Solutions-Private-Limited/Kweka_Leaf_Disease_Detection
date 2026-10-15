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
import re
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from pymongo.database import Database

from schemas.leaf_advisory import (
    AdvisoryHistoricalDiagnosisItem,
    LeafAdvisoryRequest,
    SeasonalRiskAssessment,
    LeafAdvisoryResponse
)
from schemas.nacl_catalog import NACLProductRecommendation
from db.nacl_product_db import query_nacl_products, get_db
from services.leaf_disease.nacl_recommendation_engine import validate_nacl_product_match

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


def _parse_dosage_number(dosage_str: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
    """Extracts numerical dosage and unit (ml or gm or kg) per acre from label string."""
    if not dosage_str or "refer" in dosage_str.lower():
        return None, None
    clean = dosage_str.replace("–", "-").replace("—", "-")
    range_match = re.search(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(ml|gm|g|kg|l|lit)', clean, re.I)
    if range_match:
        val1 = float(range_match.group(1))
        val2 = float(range_match.group(2))
        unit = range_match.group(3).lower()
        return (val1 + val2) / 2.0, unit
    single_match = re.search(r'(\d+(?:\.\d+)?)\s*(ml|gm|g|kg|l|lit)', clean, re.I)
    if single_match:
        return float(single_match.group(1)), single_match.group(2).lower()
    return None, None


def _parse_pack_size_in_base_units(pack_str: str) -> Tuple[Optional[float], Optional[str]]:
    """Converts a pack string like '500ml', '1lt', '250gm', '1 Kg' into base units (ml or gm)."""
    p_clean = pack_str.strip().lower().replace(" ", "")
    m_lit = re.match(r'(\d+(?:\.\d+)?)(?:lt|l|liter|litres)', p_clean)
    if m_lit:
        return float(m_lit.group(1)) * 1000.0, "ml"
    m_ml = re.match(r'(\d+(?:\.\d+)?)ml', p_clean)
    if m_ml:
        return float(m_ml.group(1)), "ml"
    m_kg = re.match(r'(\d+(?:\.\d+)?)(?:kg|kilo)', p_clean)
    if m_kg:
        return float(m_kg.group(1)) * 1000.0, "gm"
    m_gm = re.match(r'(\d+(?:\.\d+)?)(?:gm|g)', p_clean)
    if m_gm:
        return float(m_gm.group(1)), "gm"
    return None, None


def _calculate_commercial_packs(total_needed: float, unit: str, pack_sizes: List[str]) -> str:
    """Calculates realistic commercial bottle / pack counts for dealer purchase."""
    if not pack_sizes:
        return f"{total_needed:.1f} {unit}"
    
    parsed_packs: List[Tuple[float, str]] = []
    for ps in pack_sizes:
        val, u = _parse_pack_size_in_base_units(ps)
        if val is not None and u == unit:
            parsed_packs.append((val, ps))
    
    if not parsed_packs:
        return f"{total_needed:.1f} {unit}"
        
    parsed_packs.sort(key=lambda x: x[0], reverse=True)
    
    # Exact match check
    for val, label in parsed_packs:
        if abs(val - total_needed) < 1e-3:
            return f"1 × {label} pack"
            
    rem = total_needed
    chosen = []
    for val, label in parsed_packs:
        if rem <= 0:
            break
        count = int(rem // val)
        if count > 0:
            chosen.append(f"{count} × {label}")
            rem -= count * val
            
    if rem > 0:
        smallest_fitting = None
        for val, label in reversed(parsed_packs):
            if val >= rem:
                smallest_fitting = label
                break
        if smallest_fitting:
            chosen.append(f"1 × {smallest_fitting}")
        else:
            chosen.append(f"1 × {parsed_packs[-1][1]}")
            
    return " + ".join(chosen)


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
        query: Dict[str, Any] = {"source": {"$ne": "LEAF_ADVISORY"}}
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
                if image_url and isinstance(image_url, str) and image_url.startswith("blob:"):
                    parent_id = doc.get("parent_analysis_id")
                    image_url = None
                    if parent_id:
                        try:
                            parent_doc = self.db[INSPECTIONS_COLLECTION].find_one({"$or": [{"analysis_id": parent_id}, {"_id": parent_id}]})
                            if parent_doc:
                                p_img = parent_doc.get("image_url") or parent_doc.get("thumbnail")
                                if p_img and isinstance(p_img, str) and not p_img.startswith("blob:"):
                                    image_url = p_img
                        except Exception:
                            pass

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
        Strict zero-hallucination verification: recommends only verified matching products.
        """
        advisory_id = f"adv_{uuid.uuid4().hex[:12]}"
        timestamp_str = datetime.now(timezone.utc).isoformat()

        crop_clean = request.crop_name.strip()
        disease_clean = (request.disease_name or "").strip()
        pest_clean = (request.pest_name or "").strip()
        geo_clean = (request.geolocation or "").strip() if request.geolocation else None
        season_clean = (request.season or "").strip() if request.season else None

        # 1. Retrieve strictly matching NACL Agrochemical Products (Zero Hallucination)
        matched_recommendations = self._retrieve_nacl_products(
            crop_name=crop_clean,
            disease_name=disease_clean,
            pest_name=pest_clean
        )

        # 2. Acreage Bottle & Dilution Calculations and Safety Badges
        self._calculate_acreage_and_safety_dosages(matched_recommendations, request)

        # 3. Determine Escalation Triggers
        escalation_required = False
        escalation_reason = None
        if request.severity_level and "severe" in request.severity_level.lower():
            escalation_required = True
            escalation_reason = "Severe foliar damage (>30% canopy area). Immediate emergency intervention and field agronomist inspection required."
        elif request.previous_treatment and "ineffective" in request.previous_treatment.lower():
            escalation_required = True
            escalation_reason = "Prior chemical spray was reported ineffective. Suspected chemical resistance or improper application calibration."
        elif request.onset_days and ">1 week" in request.onset_days:
            escalation_required = True
            escalation_reason = "Prolonged active infection (>1 week duration) with secondary pathogen spread."

        # 4. Synthesize Scientifically Verified Combination Guidance
        comb_parts = []
        if disease_clean:
            has_premix = any("chlorothalonil" in (r.active_ingredient or "").lower() and "azoxystrobin" in (r.active_ingredient or "").lower() for r in matched_recommendations)
            if has_premix:
                comb_parts.append("Dual-Action Pre-Mix: Formulations like Kadak combine systemic strobilurin with multi-site contact chlorothalonil for built-in resistance prevention and dual translaminar + contact barrier.")
            elif matched_recommendations:
                comb_parts.append("Curative + Protective Tank Mix: For aggressive foliar spread, tank-mix the recommended systemic product with a multi-site contact protectant (e.g. Mancozeb @ 2 g/L) to prevent resistance and provide instant surface knockdown.")
            else:
                comb_parts.append("Foliar Protection: Use protective copper-based sprays (Copper Oxychloride 50% WP @ 2.5 g/L) or certified biocontrol agents (Trichoderma viride @ 5 g/L) as a safe preventive combination.")

        if request.recent_weather and any(w in request.recent_weather.lower() for w in ("rain", "humid", "overcast", "wet")):
            comb_parts.append("Weather Rainfastness Adjuvant: Due to high humidity or rain risk, combine a non-ionic spreader/sticker (organosilicone adjuvant @ 0.5 ml/L) to prevent chemical wash-off.")

        if request.previous_treatment and "ineffective" in request.previous_treatment.lower():
            comb_parts.append("Resistance Management Rotation: The previous spray failed. Do NOT repeat the same active ingredient. Rotate to an alternate FRAC/IRAC chemical class and tank-mix with a multi-site contact protectant.")

        if pest_clean and disease_clean:
            comb_parts.append("Dual Vector & Disease Control: If insect feeding co-occurs with foliar infection, apply a compatible insecticide tank-mix to halt pest vectors spreading secondary infections.")

        combination_guidance = " • ".join(comb_parts) if comb_parts else None

        # 5. Build Intake Summary Record
        intake_summary = {
            "growth_stage": request.growth_stage or "Not specified",
            "onset_days": request.onset_days or "Not specified",
            "recent_weather": request.recent_weather or "Not specified",
            "previous_treatment": request.previous_treatment or "None reported",
            "area_sown": f"{request.area_sown} {request.area_unit or 'acres'}" if request.area_sown else "Not specified",
            "sowing_date": request.sowing_date or "Not specified",
            "crop_variety": request.crop_variety or "Standard / Unspecified",
            "plant_part_affected": ", ".join(request.plant_part_affected) if request.plant_part_affected else "Foliage",
            "irrigation_condition": request.irrigation_condition or "Normal",
            "severity_level": request.severity_level or "Not specified",
            "farmer_name": request.farmer_name,
            "farmer_phone": request.farmer_phone,
            "farmer_notes": request.farmer_notes,
            "gps_coordinates": request.gps_coordinates,
        }

        # Area calculation summary
        area_calculation_summary = None
        if request.area_sown and request.area_sown > 0:
            unit = request.area_unit or "acres"
            acres = (request.area_sown * 2.47105) if unit.lower() in ("hectares", "ha", "hectare") else request.area_sown
            water_liters = int(round(acres * 200))
            tanks = max(1, int(round(water_liters / 15)))
            area_calculation_summary = (
                f"Field Area: {request.area_sown:.1f} {unit} ({acres:.1f} acres). Total Dilution: {water_liters} Liters water "
                f"(~{tanks} knapsack sprayers of 15L). Commercial bottle packaging requirements calculated per product below."
            )

        # 6. Synthesize Gemini Agronomist Advisory
        gemini_result = self._synthesize_gemini_advisory(
            crop_name=crop_clean,
            disease_name=disease_clean,
            pest_name=pest_clean,
            geolocation=geo_clean,
            season=season_clean,
            recommendations=matched_recommendations,
            request=request,
            combination_guidance=combination_guidance
        )

        seasonal_risk = SeasonalRiskAssessment(
            season_name=season_clean or "General / All Season",
            geolocation_name=geo_clean or "General Agricultural Region",
            climate_factors=gemini_result["climate_factors"],
            disease_pressure_level=gemini_result["disease_pressure_level"],
            weather_spray_window_advice=gemini_result["weather_spray_window_advice"],
        )

        image_url = request.image_url
        if image_url and isinstance(image_url, str) and image_url.startswith("blob:"):
            image_url = None

        if not image_url and request.analysis_id:
            try:
                hist_doc = self.db[INSPECTIONS_COLLECTION].find_one({
                    "$or": [{"analysis_id": request.analysis_id}, {"_id": request.analysis_id}]
                })
                if hist_doc:
                    p_img = hist_doc.get("image_url") or hist_doc.get("thumbnail")
                    if p_img and isinstance(p_img, str) and not p_img.startswith("blob:"):
                        image_url = p_img
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
            intake_summary=intake_summary,
            area_calculation_summary=area_calculation_summary,
            escalation_required=escalation_required,
            escalation_reason=escalation_reason,
            combination_guidance=combination_guidance
        )

    def _calculate_acreage_and_safety_dosages(
        self,
        recommendations: List[NACLProductRecommendation],
        request: LeafAdvisoryRequest
    ) -> None:
        """Enriches verified recommendations with acreage bottle counts, knapsack water volumes, and safety badges."""
        area = request.area_sown
        unit = (request.area_unit or "acres").lower()
        acres = (area * 2.47105) if unit in ("hectares", "ha", "hectare") and area else area

        for r in recommendations:
            # 1. Standard statutory label dosage rate
            r.standard_label_dosage = r.recommended_dosage if r.recommended_dosage and "refer" not in r.recommended_dosage.lower() else "Refer to official label instructions"

            # 2. General Safety, PHI, REI, PPE
            r.rei_hours = 24
            r.ppe_guidelines = (
                "Wear chemical-resistant nitrile gloves, safety goggles, and an N95 particulate mask during "
                "handling and application. Avoid spraying against wind or near drinking water sources."
            )

            # 3. Growth stage safety
            stage_clean = (request.growth_stage or "").lower()
            if "flower" in stage_clean:
                r.bee_toxicity_warning = (
                    "POLLINATOR SAFETY ALERT: Crop is in active flowering stage. Do NOT spray during peak bee foraging hours "
                    "(9:00 AM - 4:00 PM). Apply strictly at dusk/late evening to protect honeybees and pollinators."
                )
                r.phi_days = 14
            elif any(w in stage_clean for w in ("fruit", "matur", "harvest")):
                r.phi_days = 7
                if not r.bee_toxicity_warning:
                    r.bee_toxicity_warning = "Pre-Harvest Interval (PHI): Observe statutory harvest interval before picking produce."
            else:
                r.phi_days = 14

            # 4. Combination / Tank-Mix Partner Recommendation (Strict Non-Contradictory Policy)
            p_name_lower = r.product_name.lower()
            p_ai_lower = (r.active_ingredient or "").lower()
            weather_clean = (request.recent_weather or "").lower()

            if "kadak" in p_name_lower or ("azoxystrobin" in p_ai_lower and "chlorothalonil" in p_ai_lower):
                r.combination_partner = (
                    "Factory Pre-Mix (Zero Tank Conflict): Pre-formulated Azoxystrobin + Chlorothalonil provides built-in "
                    "systemic translaminar and multi-site contact protection. Do NOT add other fungicides to the tank."
                )
            elif any(s in p_ai_lower for s in ("carbendazim", "hexaconazole", "thifluzamide")) or "zen" in p_name_lower or "mass" in p_name_lower or "kazan" in p_name_lower:
                r.combination_partner = (
                    "Compatible Synergistic Tank-Mix: Mix this systemic product with Mancozeb 75% WP (Zeb) @ 2.0–2.5 gm/L water. "
                    "Mixing Order: Dissolve Mancozeb powder completely in 50% water first, then add the liquid product. Agitate thoroughly."
                )
            elif r.category == "Fungicide":
                r.combination_partner = (
                    "Sequential Application (Do NOT Tank-Mix): To avoid physical incompatibility or chemical scorch, "
                    "apply this product first as a standalone spray. If follow-up protection is needed, apply Mancozeb 75% WP @ 2.0 gm/L "
                    "separately 7–10 days later. Do not mix concentrates directly in the same tank."
                )
            else:
                r.combination_partner = (
                    "Standalone Target Application: Apply strictly as an individual foliar spray at official label rates. "
                    "Avoid multi-chemical tank mixing to eliminate phytotoxicity risks."
                )

            if any(w in weather_clean for w in ("rain", "humid", "overcast", "wet")):
                adjuvant_note = "Rainy/Humid Adjuvant: Add 0.5 ml/L non-ionic organosilicone spreader/sticker as the FINAL component after chemicals are fully dissolved."
                r.combination_partner = f"{r.combination_partner} | {adjuvant_note}"

            # 5. Acreage-based calculations (only if acreage provided)
            if acres and acres > 0:
                water_liters = int(round(acres * 200))
                knapsack_tanks = max(1, int(round(water_liters / 15)))
                r.calculated_total_water = f"{water_liters} Liters water (~{knapsack_tanks} knapsack sprayers of 15L)"

                dosage_val, dosage_unit = _parse_dosage_number(r.recommended_dosage)
                if dosage_val and dosage_unit:
                    base_val = dosage_val * 1000.0 if dosage_unit in ("kg", "l", "lit") else dosage_val
                    base_unit = "gm" if dosage_unit in ("kg", "gm", "g") else "ml"
                    total_chem = base_val * acres

                    if total_chem >= 1000:
                        vol_display = f"{total_chem / 1000.0:.2f} {'kg' if base_unit == 'gm' else 'L'} ({total_chem:.0f} {base_unit})"
                    else:
                        vol_display = f"{total_chem:.1f} {base_unit}"

                    r.calculated_total_dosage = vol_display
                    r.calculated_bottles = _calculate_commercial_packs(total_chem, base_unit, r.pack_sizes)
                else:
                    r.calculated_total_dosage = f"Dilute as per label per-acre instructions for {acres:.1f} {unit}"
                    r.calculated_bottles = "Purchase commercial packaging according to official label dilution"

    def _retrieve_nacl_products(
        self,
        crop_name: str,
        disease_name: str,
        pest_name: str
    ) -> List[NACLProductRecommendation]:
        """
        Deterministically queries, validates, and ranks verified NACL catalog products.
        STRICT ZERO-HALLUCINATION ENFORCEMENT:
          - Only products verified for this crop + target disease/pest are accepted.
          - Absolutely NO broad random fallback dumps. If no products are registered, returns empty list.
        """
        recs: List[NACLProductRecommendation] = []
        seen_ids = set()

        # Step 1: Query fungicides matching disease/crop
        if disease_name:
            disease_prods = query_nacl_products(crop_name=crop_name, category="Fungicides", db=self.db)
            for p in disease_prods:
                p_id = p.get("product_id")
                if not p_id or p_id in seen_ids:
                    continue

                val_report = validate_nacl_product_match(p, crop_name, disease_name)
                if val_report["product_verified"]:
                    seen_ids.add(p_id)
                    recs.append(
                        NACLProductRecommendation(
                            product_id=p_id,
                            product_name=p.get("product_name", p_id.title()),
                            category="Fungicide",
                            product_url=p.get("product_url", "https://naclind.com/products/"),
                            active_ingredient=p.get("active_ingredient"),
                            match_type=val_report["verification_status"],
                            verification_status=val_report["verification_status"],
                            dosage_verified=val_report["dosage_verified"],
                            recommended_dosage=val_report["recommended_dosage"],
                            match_rationale=f"Verified NACL fungicide registration for {crop_name} against {disease_name}.",
                            verification_reason=val_report["rejection_reason"],
                            pack_sizes=p.get("pack_sizes", []),
                            frac_group=None
                        )
                    )

        # Step 2: Query insecticides matching pest/crop
        if pest_name:
            pest_prods = query_nacl_products(crop_name=crop_name, category="Insecticides", db=self.db)
            for p in pest_prods:
                p_id = p.get("product_id")
                if not p_id or p_id in seen_ids:
                    continue

                val_report = validate_nacl_product_match(p, crop_name, pest_name)
                if val_report["product_verified"]:
                    seen_ids.add(p_id)
                    recs.append(
                        NACLProductRecommendation(
                            product_id=p_id,
                            product_name=p.get("product_name", p_id.title()),
                            category="Insecticide",
                            product_url=p.get("product_url", "https://naclind.com/products/"),
                            active_ingredient=p.get("active_ingredient"),
                            match_type=val_report["verification_status"],
                            verification_status=val_report["verification_status"],
                            dosage_verified=val_report["dosage_verified"],
                            recommended_dosage=val_report["recommended_dosage"],
                            match_rationale=f"Verified NACL insecticide registration for {crop_name} against {pest_name}.",
                            verification_reason=val_report["rejection_reason"],
                            pack_sizes=p.get("pack_sizes", []),
                            frac_group=None
                        )
                    )

        # CRITICAL SAFETY DIRECTIVE:
        # ABSOLUTELY NO BROAD CATEGORY FALLBACK!
        # If no products match, recs remains empty. We never hallucinate or recommend random chemicals.

        # Rank verified remedies by beneficial suitability
        target_str = (disease_name or pest_name or "").lower()
        crop_clean = (crop_name or "").lower()

        scored: List[Tuple[int, NACLProductRecommendation]] = []
        for r in recs:
            score = 0
            if r.match_type in ("VERIFIED_DISEASE_MATCH", "VERIFIED_PEST_MATCH", "VERIFIED_DIRECT_MATCH"):
                score += 60
            elif r.verification_status == "VERIFIED_CROP_TARGET_MATCH":
                score += 45
            else:
                score += 15

            if r.dosage_verified and r.recommended_dosage and "refer" not in r.recommended_dosage.lower():
                score += 30

            if crop_clean and crop_clean in r.match_rationale.lower():
                score += 20

            if target_str and any(w in r.match_rationale.lower() for w in target_str.split() if len(w) > 3):
                score += 15

            scored.append((score, r))

        scored.sort(key=lambda x: x[0], reverse=True)

        ranked_recs: List[NACLProductRecommendation] = []
        for idx, (_, r) in enumerate(scored[:4]):
            rank = idx + 1
            r.efficacy_rank = rank
            if rank == 1:
                r.benefit_badge = "Rank #1 • Top Pick"
                r.benefit_reason = f"Most beneficial verified remedy with registered target control for {crop_name}."
            elif rank == 2:
                r.benefit_badge = "Rank #2 • High Efficacy Alternative"
                r.benefit_reason = "Secondary curative treatment offering systemic foliar protection."
            elif rank == 3:
                r.benefit_badge = "Rank #3 • Broad-Spectrum Option"
                r.benefit_reason = "Complementary broad-spectrum pathogen suppression."
            else:
                r.benefit_badge = f"Rank #{rank} • Supportive Option"
                r.benefit_reason = "Supplementary protective remedy from NACL verified registrations."
            ranked_recs.append(r)

        return ranked_recs

    def _synthesize_gemini_advisory(
        self,
        crop_name: str,
        disease_name: str,
        pest_name: str,
        geolocation: Optional[str],
        season: Optional[str],
        recommendations: List[NACLProductRecommendation],
        request: Optional[LeafAdvisoryRequest] = None,
        combination_guidance: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calls Gemini with crop, diagnosis, rich intake parameters, and verified products to produce tailored advice."""
        client = _get_gemini_client()

        products_text = ""
        for r in recommendations:
            dosage = r.recommended_dosage or "Refer to product label"
            badge = r.benefit_badge or f"Rank #{r.efficacy_rank}"
            comb = f" (Recommended Combination: {r.combination_partner})" if r.combination_partner else ""
            products_text += f"- [{badge}] {r.product_name} ({r.category}): Active ingredient '{r.active_ingredient or 'Formulated Agrochemical'}'. Prescribed Dosage: {dosage}{comb}. Beneficial Rationale: {r.benefit_reason or r.match_rationale}.\n"

        geo_desc = geolocation if geolocation else "General agricultural zone (unspecified region)"
        season_desc = season if season else "Standard growing season (unspecified climate)"

        growth_stage = request.growth_stage if request and request.growth_stage else "Not specified"
        onset = request.onset_days if request and request.onset_days else "Not specified"
        weather = request.recent_weather if request and request.recent_weather else "Not specified"
        prev_treatment = request.previous_treatment if request and request.previous_treatment else "None reported"
        area_sown_desc = f"{request.area_sown} {request.area_unit or 'acres'}" if request and request.area_sown else "Not specified"
        variety = request.crop_variety if request and request.crop_variety else "Unspecified variety"
        severity = request.severity_level if request and request.severity_level else "Moderate"

        top_name = recommendations[0].product_name if recommendations else None
        alt_name = recommendations[1].product_name if len(recommendations) > 1 else None

        # Honest fallback data without fake product names
        if top_name:
            summary_fallback = (
                f"For the protection of {crop_name} affected by {disease_name or pest_name or 'foliar stress'}, "
                f"the top recommended remedy is {top_name}, which provides high beneficial efficacy against the identified symptoms. "
                f"An integrated crop management approach combining cultural sanitation and targeted foliar application is recommended. "
                f"Ensure even canopy coverage, avoid application during extreme heat, and follow prescribed label dosages."
            )
            chem_fallback = [
                f"Prioritize applying {top_name} (Rank #1 Top Pick) at early symptom onset for maximum curative control.",
                f"If secondary flushes appear or sequential spraying is needed, alternate with {alt_name or 'an approved rotational product'}." if alt_name else "Follow statutory label instructions for repeat application intervals.",
                "Use flat-fan nozzles at 30-40 PSI pressure with 200 L water per acre for uniform foliar droplet deposition."
            ]
        else:
            summary_fallback = (
                f"For {crop_name} affected by {disease_name or pest_name or 'foliar stress'}, no registered NACL agrochemical "
                f"product directly matches this specific pathogen and host crop combination in our verified catalog. "
                f"To protect your crop from chemical injury (phytotoxicity) and avoid ineffective pesticide use, we strictly avoid "
                f"recommending unverified or off-label chemicals. Focus immediately on the cultural sanitation, nutritional balance, "
                f"and biological remedies outlined below."
            )
            chem_fallback = [
                "No registered NACL chemical product directly targets this condition on this host crop.",
                "Consult your local agricultural university extension officer (KVK) for regional chemical recommendations if symptoms progress.",
                "Do not apply off-label chemicals without expert verification to avoid crop phytotoxicity and chemical residue."
            ]

        fallback_data = {
            "climate_factors": (
                f"Under {season_desc} in {geo_desc} with recent weather '{weather}', microclimate humidity and temperature strongly influence "
                f"pathogen spore germination and insect feeding rates. Maintain constant vigilance during wet canopy periods."
            ),
            "disease_pressure_level": "HIGH" if (severity and "severe" in severity.lower()) else ("MODERATE" if (disease_name or pest_name) else "LOW"),
            "weather_spray_window_advice": (
                "Apply foliar treatments during calm early morning or late afternoon/dusk hours. "
                "Avoid spraying during high midday temperatures or when rain is expected within 2-3 hours."
            ),
            "ai_advisory_summary": summary_fallback,
            "cultural_remedies": [
                f"Prune and destroy heavily infected lower leaves showing visible {disease_name or 'damage'} to reduce pathogen inoculum.",
                f"Improve field drainage and plant spacing to optimize air circulation and reduce canopy relative humidity.",
                f"Eliminate alternate weed hosts and wild volunteer plants along bunds and field perimeters.",
                f"Avoid excessive nitrogenous fertilizer application that promotes lush, tender foliage highly vulnerable to attack."
            ],
            "chemical_management": chem_fallback
        }

        if not client:
            return fallback_data

        models_to_try = [
            os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]

        prompt = f"""You are a senior agricultural agronomist and plant pathologist specializing in Indian and global crop protection.
A farmer has requested expert advisory and treatment remedies for their crop.

DIAGNOSTIC & FIELD INTAKE DETAILS:
- Crop: {crop_name} (Variety: {variety})
- Diagnosed Disease / Pathology: {disease_name or 'None identified'}
- Diagnosed Insect Pest: {pest_name or 'None identified'}
- Growth Stage: {growth_stage}
- Onset: {onset}
- Recent Climate / Weather: {weather}
- Previous Treatment History: {prev_treatment}
- Severity Level: {severity}
- Area Sown: {area_sown_desc}
- Geolocation / Region: {geo_desc}
- Season: {season_desc}
- Combination / Tank-Mix Advice Identified: {combination_guidance or 'None specified'}

VERIFIED NACL AGROCHEMICAL CATALOG REMEDIES (Deterministically verified for this crop and target):
{products_text if products_text else 'NO REGISTERED NACL PRODUCTS IN CATALOG FOR THIS CROP AND PATHOGEN.'}

CRITICAL AGRONOMIC SAFETY & ZERO-HALLUCINATION DIRECTIVES:
1. NEVER INVENT OR HALLUCINATE CHEMICAL PRODUCTS. Recommending the wrong chemical causes severe crop damage (phytotoxicity), kills pollinating bees, or leaves farmers with ruined harvests.
2. If verified NACL products ARE listed above:
   - Base chemical recommendations strictly on the provided list and their registered label claims.
   - Detail how to use the Rank #1 remedy and when to rotate.
   - COMBINATIONS & TANK-MIX SAFETY RULES:
     * When suggesting combinations of multiple products (e.g., using X ml/L of one product with Y gm/L of another), make sure those combos are strictly non-contradictory, physically compatible, and chemically safe (e.g. systemic fungicide + Mancozeb contact protectant, or non-ionic sticker adjuvant @ 0.5 ml/L in wet weather).
     * Mixing Order: Always dissolve powders (WP/WDG) first, followed by liquid suspensions (SC/EC), and adjuvants last.
     * CRITICAL: If you are NOT 100% confident about the tank-mix compatibility of two products, DO NOT suggest mixing them in the same spray tank! Instead, mention them STRICTLY SEPARATELY as a sequential spray schedule (e.g., "Apply Product A on Day 1; if needed, spray Product B separately after 7–10 days").
     * Never advise tank-mixing copper or sulfur with incompatible emulsifiable concentrates or alkaline sprays.
3. If NO registered products are listed:
   - State honestly and transparently that no registered NACL agrochemical directly targets this specific condition on this host crop.
   - DO NOT suggest random chemical brand names.
   - Provide safe cultural, biological, and agronomic management practices (e.g., sanitation, spacing, copper fungicides, Trichoderma/Pseudomonas bio-agents).
4. If crop is in 'Flowering' stage, strictly emphasize honeybee pollinator safety (spray only at dusk/evening).

Respond ONLY with a valid JSON object matching this schema:
{{
  "climate_factors": "2-3 sentences explaining how this specific season, region, and recent weather impact pathogen lifecycle or insect pressure.",
  "disease_pressure_level": "HIGH or MODERATE or LOW",
  "weather_spray_window_advice": "Specific recommendation on optimal spraying time of day, rainfastness window, and weather precautions.",
  "ai_advisory_summary": "2-3 paragraphs providing an agronomist advisory explaining what the farmer is facing, why the recommended strategy is effective, and what immediate action is required.",
  "cultural_remedies": [
    "Practical cultural/agronomic remedy 1 (drainage, spacing, sanitation)",
    "Practical cultural/agronomic remedy 2",
    "Practical cultural/agronomic remedy 3",
    "Practical cultural/agronomic remedy 4"
  ],
  "chemical_management": [
    "Specific instruction on chemical treatment (or cultural/biological measures if no chemical is registered)",
    "Tank-mix or combination guidance (systemic + contact or adjuvant sticker if applicable)",
    "Spraying safety, calibration, and pollinator precautions"
  ]
}}
Do not invent unverified brands outside of the provided NACL products.
Do not mention FRAC or IRAC code numbers.
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
                            "disease_pressure_level": parsed.get("disease_pressure_level", fallback_data["disease_pressure_level"]),
                            "weather_spray_window_advice": parsed.get("weather_spray_window_advice", fallback_data["weather_spray_window_advice"]),
                            "ai_advisory_summary": parsed.get("ai_advisory_summary", fallback_data["ai_advisory_summary"]),
                            "cultural_remedies": parsed.get("cultural_remedies", fallback_data["cultural_remedies"]),
                            "chemical_management": parsed.get("chemical_management", fallback_data["chemical_management"]),
                        }
            except Exception as ex:
                logger.warning(f"Gemini advisory generation with model {m} failed: {ex}")
                continue

        return fallback_data
