"""
cross_validation.py — Schemas for Cross-Validation & Diagnostic Reliability Engine
-----------------------------------------------------------------------------------
Defines standardized diagnostic statuses, independent evidence structures,
host-pest compatibility models, contradiction records, and verification routing contracts.
"""

from enum import Enum
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class DiagnosticStatus(str, Enum):
    """
    Standardized diagnostic status enum for all diagnostic modules.
    Keeps detection status strictly separate from confidence scores.
    """
    CONFIRMED = "CONFIRMED"
    SUSPECTED = "SUSPECTED"
    UNCERTAIN = "UNCERTAIN"
    NOT_DETECTED = "NOT_DETECTED"
    UNABLE_TO_ASSESS = "UNABLE_TO_ASSESS"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"


class HostPestRelationshipType(str, Enum):
    ESTABLISHED_HOST = "ESTABLISHED_HOST"
    REPORTED_HOST = "REPORTED_HOST"
    UNEXPECTED_HOST = "UNEXPECTED_HOST"
    UNCERTAIN_RELATIONSHIP = "UNCERTAIN_RELATIONSHIP"
    NOT_EVALUATED = "NOT_EVALUATED"


class HostPestCompatibilityStatus(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class HostPestCompatibilityResult(BaseModel):
    """
    Structured outcome of biological host-pest plausibility validation.
    Used strictly to evaluate plausibility, never to overwrite model predictions.
    """
    compatibility_status: HostPestCompatibilityStatus
    pest_canonical_name: Optional[str] = None
    pest_scientific_name: Optional[str] = None
    host_crop_name: Optional[str] = None
    relationship_type: HostPestRelationshipType
    relationship_provenance: Optional[str] = None
    biological_family: Optional[str] = None
    notes: str
    limitations: str = (
        "Biological host range database is incomplete. A missing entry indicates an UNKNOWN "
        "relationship, never definitive proof of incompatibility."
    )


class ContradictionItem(BaseModel):
    """Detailed record of a detected anomaly or contradiction across diagnostic modules."""
    category: str
    code: str
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    message: str
    affected_categories: List[str]
    evidence_detail: str


class CategoryValidationDetail(BaseModel):
    """
    Preserves original raw prediction while providing independent calibrated status,
    confidence interpretation, and evidence reasoning.
    """
    category_name: str
    predicted_label: str
    scientific_name: Optional[str] = None
    original_model_score: Optional[float] = None
    confidence_source: str
    confidence_interpretation: str
    diagnostic_status: DiagnosticStatus
    confidence_gate_passed: bool
    evidence_summary: str
    warnings: List[str] = Field(default_factory=list)
    raw_evidence_retained: Dict[str, Any] = Field(default_factory=dict)


class CandidateReviewItem(BaseModel):
    category: str
    candidate_label: str
    reason_for_review: str


class ComparisonStatus(str, Enum):
    AGREEMENT = "AGREEMENT"
    DISAGREEMENT = "DISAGREEMENT"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNAVAILABLE = "UNAVAILABLE"


class AntigravityCategoryAssessment(BaseModel):
    """Independent category evaluation without assuming other model predictions."""
    category: str
    primary_candidate: str
    alternative_candidates: List[str] = Field(default_factory=list)
    visible_evidence: str
    unverified_distinguishing_features: str
    confidence_assessment: str
    suitable_for_confirmation: bool = False


class AntigravityIndependentAssessment(BaseModel):
    """Complete independent multi-category evaluation."""
    crop: AntigravityCategoryAssessment
    pest: AntigravityCategoryAssessment
    leaf_damage: AntigravityCategoryAssessment
    disease: AntigravityCategoryAssessment
    weed: AntigravityCategoryAssessment
    summary: str
    limitations: str = (
        "Antigravity visual analysis evaluates morphological patterns from submitted imagery and metadata. "
        "It does not fabricate numerical probabilities and cannot replace high-resolution botanical/entomological field inspection."
    )


class CategoryComparisonRecord(BaseModel):
    """Structured cross-system comparison for a diagnostic category."""
    category: str
    antigravity_assessment: str
    plantnet_assessment: Optional[str] = None
    ip102_assessment: Optional[str] = None
    gemini_assessment: Optional[str] = None
    status: ComparisonStatus
    agreement_summary: str
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    known_model_limitations: List[str] = Field(default_factory=list)
    biological_plausibility: str
    adjudicated_decision: DiagnosticStatus
    traceable_explanation: str
    requires_expert_review: bool = False


class ConditionalGeminiVerificationPrompt(BaseModel):
    """Formulated prompt and targeted questions when conditional Gemini verification is indicated."""
    triggered: bool
    trigger_reason: Optional[str] = None
    targeted_questions: List[str] = Field(default_factory=list)
    candidate_predictions_payload: Dict[str, Any] = Field(default_factory=dict)
    prompt_text: Optional[str] = None
    evaluation_against_evidence: Optional[str] = None


class FinalAdjudicationReport(BaseModel):
    """Final diagnostic report synthesizing all evidence, decisions, and traceability."""
    best_supported_crop: Dict[str, Any]
    best_supported_pest: Dict[str, Any]
    observed_damage: Dict[str, Any]
    disease_findings: Dict[str, Any]
    weed_findings: Dict[str, Any]
    host_pest_compatibility_summary: str
    final_decisions: Dict[str, DiagnosticStatus]
    traceable_explanations: Dict[str, str]
    further_actions_needed: List[str]


class VerificationRoutingDecision(BaseModel):
    """
    Deterministic verification routing recommendation without invoking external API calls.
    Represents future Gemini verification as disabled-by-default configuration.
    """
    verification_required: bool
    triggers: List[str] = Field(default_factory=list)
    categories_needing_review: List[str] = Field(default_factory=list)
    conflicting_or_missing_evidence: List[str] = Field(default_factory=list)
    recommended_candidates_to_examine: List[CandidateReviewItem] = Field(default_factory=list)
    gemini_feature_enabled: bool = False
    gemini_routing_status: Literal["DISABLED", "PENDING", "COMPLETED", "ERROR"] = "DISABLED"
    gemini_action_summary: str = (
        "Verification routing evaluated deterministically. External Gemini API calls are disabled "
        "by default in this phase. Triggers and candidate review hypotheses are recorded without external requests."
    )


class CrossValidationResult(BaseModel):
    """
    Complete evidence-based cross-validation output across all four diagnostic streams.
    """
    engine_version: str = "1.1.0"
    crop_validation: CategoryValidationDetail
    disease_validation: CategoryValidationDetail
    pest_validation: CategoryValidationDetail
    weed_validation: CategoryValidationDetail
    host_pest_compatibility: HostPestCompatibilityResult
    detected_contradictions: List[ContradictionItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    verification_routing: VerificationRoutingDecision
    overall_reliability_summary: str
    timestamp: str

    # Extended Independent Assessment, Comparison & Adjudication Layers
    antigravity_assessment: Optional[AntigravityIndependentAssessment] = None
    category_comparisons: List[CategoryComparisonRecord] = Field(default_factory=list)
    conditional_gemini_query: Optional[ConditionalGeminiVerificationPrompt] = None
    final_adjudication_report: Optional[FinalAdjudicationReport] = None

