import { apiClient } from './client';
import { ImageValidationDetail } from './leafDisease';

export interface CropIdentificationTestResult {
  status: 'CONFIRMED' | 'UNCERTAIN' | 'SUSPECTED' | 'NEEDS_VERIFICATION' | 'UNSUPPORTED' | 'MODEL_UNAVAILABLE' | 'ERROR';
  crop_name: string;
  scientific_name?: string;
  common_names: string[];
  confidence?: number;
  is_agricultural_crop?: boolean;
  plant_type?: string;
  quality_warning?: string;
  provider: string;
  is_operational: boolean;
  message: string;
}

export interface DiseaseCandidateTestItem {
  disease_name: string;
  confidence?: number;
}

export interface DiseaseDetectionTestResult {
  status: 'CONFIRMED' | 'UNCERTAIN' | 'SUSPECTED' | 'NEEDS_VERIFICATION' | 'NO_DISEASE_DETECTED' | 'INVALID_CATEGORY' | 'MODEL_UNAVAILABLE' | 'ERROR';
  disease_name: string;
  common_name?: string;
  scientific_name?: string;
  confidence?: number;
  confidence_gate_passed: boolean;
  provider: string;
  is_operational: boolean;
  candidates: DiseaseCandidateTestItem[];
  message: string;
  raw_provider_finding?: string;
  raw_provider_score?: number;
  category_warning?: string;
  host_crop_compatibility?: string;
}

export interface WeedBoundingBox {
  ymin: number;
  xmin: number;
  ymax: number;
  xmax: number;
  label: string;
  confidence: number;
}

export interface DetectedWeedTestItem {
  weed_name: string;
  scientific_name?: string;
  confidence: number;
  bounding_box?: WeedBoundingBox;
  detection_type?: string;
  growth_habit?: string;
}

export interface WeedDetectionTestResult {
  status: 'CONFIRMED' | 'UNCERTAIN' | 'NO_WEED_DETECTED' | 'MODEL_UNAVAILABLE' | 'ERROR';
  detected_weeds: DetectedWeedTestItem[];
  confidence?: number;
  provider: string;
  is_operational: boolean;
  model_name?: string;
  architecture_type?: string;
  supports_bounding_boxes?: boolean;
  dataset_origin?: string;
  message: string;
}

export interface PestBoundingBoxTestItem {
  ymin: number;
  xmin: number;
  ymax: number;
  xmax: number;
  label: string;
  confidence: number;
}

export interface DetectedPestTestItem {
  pest_name: string;
  scientific_name?: string;
  pest_class_id: number;
  category: string;
  confidence: number;
  damage_type?: string;
  bounding_box?: PestBoundingBoxTestItem;
}

export interface PestDetectionTestResult {
  status: 'CONFIRMED' | 'UNCERTAIN' | 'SUSPECTED' | 'NEEDS_VERIFICATION' | 'NO_PEST_DETECTED' | 'MODEL_UNAVAILABLE' | 'ERROR';
  detected_pests: DetectedPestTestItem[];
  primary_pest?: string;
  confidence?: number;
  confidence_gate_passed: boolean;
  provider: string;
  is_operational: boolean;
  model_name: string;
  supported_classes_count: number;
  consensus_applied?: boolean;
  cross_model_verified?: boolean;
  validation_source?: string;
  original_local_confidence?: number;
  message: string;
}

export interface DetectorStatusItem {
  detector_name: string;
  provider: string;
  is_operational: boolean;
  status: 'OPERATIONAL' | 'UNAVAILABLE' | 'AWAITING_WEIGHTS';
  type: string;
  details: string;
}

export interface UnifiedTestStatusResponse {
  detectors: Record<string, DetectorStatusItem>;
}

export type DiagnosticStatus = 'CONFIRMED' | 'SUSPECTED' | 'UNCERTAIN' | 'NOT_DETECTED' | 'UNABLE_TO_ASSESS' | 'NEEDS_VERIFICATION';

export interface HostPestCompatibilityResult {
  compatibility_status: 'COMPATIBLE' | 'INCOMPATIBLE' | 'UNKNOWN' | 'NOT_APPLICABLE';
  pest_canonical_name?: string;
  pest_scientific_name?: string;
  host_crop_name?: string;
  relationship_type: 'ESTABLISHED_HOST' | 'REPORTED_HOST' | 'UNEXPECTED_HOST' | 'UNCERTAIN_RELATIONSHIP' | 'NOT_EVALUATED';
  relationship_provenance?: string;
  biological_family?: string;
  notes: string;
  limitations: string;
}

export interface ContradictionItem {
  category: string;
  code: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  message: string;
  affected_categories: string[];
  evidence_detail: string;
}

export interface CategoryValidationDetail {
  category_name: string;
  predicted_label: string;
  scientific_name?: string;
  original_model_score?: number;
  confidence_source: string;
  confidence_interpretation: string;
  diagnostic_status: DiagnosticStatus;
  confidence_gate_passed: boolean;
  evidence_summary: string;
  warnings: string[];
  raw_evidence_retained?: Record<string, any>;
}

export interface CandidateReviewItem {
  category: string;
  candidate_label: string;
  reason_for_review: string;
}

export interface VerificationRoutingDecision {
  verification_required: boolean;
  triggers: string[];
  categories_needing_review: string[];
  conflicting_or_missing_evidence: string[];
  recommended_candidates_to_examine: CandidateReviewItem[];
  gemini_feature_enabled: boolean;
  gemini_routing_status: 'DISABLED' | 'PENDING' | 'COMPLETED' | 'ERROR';
  gemini_action_summary: string;
}

export interface AntigravityCategoryAssessment {
  category: string;
  primary_candidate: string;
  alternative_candidates: string[];
  visible_evidence: string;
  unverified_distinguishing_features: string;
  confidence_assessment: string;
  suitable_for_confirmation: boolean;
}

export interface AntigravityIndependentAssessment {
  crop: AntigravityCategoryAssessment;
  pest: AntigravityCategoryAssessment;
  leaf_damage: AntigravityCategoryAssessment;
  disease: AntigravityCategoryAssessment;
  weed: AntigravityCategoryAssessment;
  summary: string;
  limitations: string;
}

export interface CategoryComparisonRecord {
  category: string;
  antigravity_assessment: string;
  plantnet_assessment?: string;
  ip102_assessment?: string;
  gemini_assessment?: string;
  status: 'AGREEMENT' | 'DISAGREEMENT' | 'PARTIALLY_SUPPORTED' | 'INSUFFICIENT_EVIDENCE' | 'UNAVAILABLE';
  agreement_summary: string;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  known_model_limitations: string[];
  biological_plausibility: string;
  adjudicated_decision: DiagnosticStatus;
  traceable_explanation: string;
  requires_expert_review: boolean;
}

export interface ConditionalGeminiVerificationPrompt {
  triggered: boolean;
  trigger_reason?: string;
  targeted_questions: string[];
  candidate_predictions_payload: Record<string, any>;
  prompt_text?: string;
  evaluation_against_evidence?: string;
}

export interface FinalAdjudicationReport {
  best_supported_crop: Record<string, any>;
  best_supported_pest: Record<string, any>;
  observed_damage: Record<string, any>;
  disease_findings: Record<string, any>;
  weed_findings: Record<string, any>;
  host_pest_compatibility_summary: string;
  final_decisions: Record<string, DiagnosticStatus>;
  traceable_explanations: Record<string, string>;
  further_actions_needed: string[];
}

export interface CrossValidationResult {
  engine_version: string;
  crop_validation: CategoryValidationDetail;
  disease_validation: CategoryValidationDetail;
  pest_validation: CategoryValidationDetail;
  weed_validation: CategoryValidationDetail;
  host_pest_compatibility: HostPestCompatibilityResult;
  detected_contradictions: ContradictionItem[];
  warnings: string[];
  verification_routing: VerificationRoutingDecision;
  overall_reliability_summary: string;
  timestamp: string;
  antigravity_assessment?: AntigravityIndependentAssessment;
  category_comparisons?: CategoryComparisonRecord[];
  conditional_gemini_query?: ConditionalGeminiVerificationPrompt;
  final_adjudication_report?: FinalAdjudicationReport;
}

export interface UnifiedTestAnalysisResponse {
  analysis_id: string;
  timestamp: string;
  image_validation: ImageValidationDetail;
  crop: CropIdentificationTestResult;
  disease: DiseaseDetectionTestResult;
  weed: WeedDetectionTestResult;
  pest?: PestDetectionTestResult;
  cross_validation?: CrossValidationResult;
  notes: string[];
}


/**
 * Uploads test image(s) (1 to 5 photos) to execute independent Crop, Disease, Pest, and Weed detection.
 * Supports optional upfront crop specification or post-diagnosis override.
 */
export async function analyzeUnifiedTest(
  fileOrFiles: File | File[],
  manualCrop?: string | null
): Promise<UnifiedTestAnalysisResponse> {
  const formData = new FormData();

  if (Array.isArray(fileOrFiles)) {
    fileOrFiles.forEach((file) => {
      formData.append('files', file);
    });
    if (fileOrFiles.length > 0) {
      formData.append('file', fileOrFiles[0]); // backward compatibility
    }
  } else if (fileOrFiles) {
    formData.append('file', fileOrFiles);
    formData.append('files', fileOrFiles);
  }

  if (manualCrop && manualCrop.trim()) {
    formData.append('manual_crop', manualCrop.trim());
  }

  const response = await apiClient.post<UnifiedTestAnalysisResponse>(
    '/api/unified-test/analyze',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
}

/**
 * Fetches the operational and readiness status of each individual detector.
 */
export async function getUnifiedTestStatus(): Promise<UnifiedTestStatusResponse> {
  const response = await apiClient.get<UnifiedTestStatusResponse>('/api/unified-test/status');
  return response.data;
}
