import { apiClient } from './client';
import { OverallImageValidationResult, CropIdentificationResult } from './leafDisease';

export interface PestBoundingBox {
  ymin: number;
  xmin: number;
  ymax: number;
  xmax: number;
  label?: string;
  confidence?: number;
}

export interface DetectedPestItem {
  pest_name: string;
  scientific_name?: string;
  pest_class_id: number;
  category: 'INSECT' | 'LARVA' | 'NYMPH' | 'ADULT' | 'PEST_DAMAGE';
  confidence: number;
  bounding_box?: PestBoundingBox;
  damage_type?: string;
  description?: string;
  affected_organs?: string[];
}

export interface PestModelInfo {
  model_id: string;
  model_name: string;
  architecture: string;
  is_operational: boolean;
  checkpoint_path?: string;
  supported_classes_count: number;
  framework: string;
  license: string;
  status_message: string;
}

export interface PestValidationResult {
  diagnosis_status: 'CONFIRMED' | 'UNCERTAIN' | 'UNSUPPORTED' | 'NO_PEST_DETECTED' | 'MODEL_UNAVAILABLE';
  calibrated_confidence: number;
  is_uncertain: boolean;
  confidence_gate_passed: boolean;
  evidence_level: 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT';
  pest_type_distinction: 'SPECIMEN_DETECTED' | 'DAMAGE_ONLY' | 'MIXED' | 'UNCERTAIN';
  crop_host_compatibility: 'COMPATIBLE' | 'POTENTIAL_MISMATCH' | 'UNRESTRICTED' | 'UNKNOWN_CROP' | 'HOST_NOT_SPECIFIED';
  image_quality_status: string;
  validation_notes: string[];
  retry_guidance?: string;
}

export interface PestDetectionAnalysisResponse {
  analysis_id: string;
  timestamp: string;
  status: 'SUCCESS' | 'UNCERTAIN' | 'UNSUPPORTED' | 'NO_PEST_DETECTED' | 'MODEL_UNAVAILABLE' | 'FAILED';
  crop: CropIdentificationResult;
  validation: OverallImageValidationResult;
  model_info: PestModelInfo;
  detected_pests: DetectedPestItem[];
  primary_pest?: DetectedPestItem;
  validation_result: PestValidationResult;
  phase_notice: string;
}

export interface PestModelStatusResponse {
  status: 'online' | 'awaiting_weights';
  model_info: PestModelInfo;
}

export interface SupportedPestClassesResponse {
  count: number;
  dataset: string;
  classes: Array<{
    id: number;
    name: string;
    scientific_name?: string;
    crops: string[];
    category: string;
    damage_type?: string;
    description?: string;
  }>;
}

/**
 * Uploads images and optional crop selection to the Phase 2 Insect & Pest Detection API.
 */
export async function analyzePests(
  files: File[],
  selectedCrop?: string
): Promise<PestDetectionAnalysisResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  if (selectedCrop && selectedCrop.trim()) {
    formData.append('selected_crop', selectedCrop.trim());
  }

  const response = await apiClient.post<PestDetectionAnalysisResponse>(
    '/api/pest-detection/analyze',
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
 * Retrieves the current operational and checkpoint status of the pest detection model.
 */
export async function getPestModelStatus(): Promise<PestModelStatusResponse> {
  const response = await apiClient.get<PestModelStatusResponse>('/api/pest-detection/status');
  return response.data;
}

/**
 * Retrieves the 102 recognized classes from the benchmark IP102 dataset.
 */
export async function getSupportedPestClasses(): Promise<SupportedPestClassesResponse> {
  const response = await apiClient.get<SupportedPestClassesResponse>('/api/pest-detection/classes');
  return response.data;
}
