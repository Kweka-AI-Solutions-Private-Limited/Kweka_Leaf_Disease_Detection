import { apiClient } from './client';
import { NACLProductRecommendation } from './leafDisease';

export interface AdvisoryHistoricalDiagnosisItem {
  analysis_id: string;
  source: string;
  timestamp: string;
  crop_name: string;
  disease_name?: string | null;
  pest_name?: string | null;
  status: string;
  confidence?: number | null;
  summary?: string | null;
  image_url?: string | null;
}

export interface LeafAdvisoryRequest {
  analysis_id?: string;
  crop_name: string;
  disease_name?: string | null;
  pest_name?: string | null;
  geolocation?: string | null; // Optional
  season?: string | null;      // Optional
  image_url?: string | null;   // Specimen leaf image
}

export interface SeasonalRiskAssessment {
  season_name: string;
  geolocation_name: string;
  climate_factors: string;
  disease_pressure_level: 'HIGH' | 'MODERATE' | 'LOW' | 'VARIABLE';
  weather_spray_window_advice: string;
}

export interface LeafAdvisoryResponse {
  advisory_id: string;
  timestamp: string;
  crop_name: string;
  disease_name?: string | null;
  pest_name?: string | null;
  geolocation?: string | null;
  season?: string | null;
  seasonal_risk: SeasonalRiskAssessment;
  nacl_products: NACLProductRecommendation[];
  ai_advisory_summary: string;
  cultural_remedies: string[];
  chemical_management: string[];
  safety_disclaimer: string;
  image_url?: string | null;
}

export interface AdvisoryOptionsResponse {
  suggested_regions: string[];
  suggested_seasons: Array<{
    name: string;
    description: string;
  }>;
}

/**
 * Fetch historical diagnoses from Leaf Scanner and Leaf Diagnosis runs
 */
export async function getAdvisoryHistory(limit = 50): Promise<AdvisoryHistoricalDiagnosisItem[]> {
  const resp = await apiClient.get<AdvisoryHistoricalDiagnosisItem[]>('/api/leaf-advisory/history', {
    params: { limit },
  });
  return resp.data;
}

/**
 * Fetch suggested regional and seasonal quick options
 */
export async function getAdvisoryOptions(): Promise<AdvisoryOptionsResponse> {
  const resp = await apiClient.get<AdvisoryOptionsResponse>('/api/leaf-advisory/options');
  return resp.data;
}

/**
 * Generate agronomist advisory taking into account optional geolocation & season
 */
export async function generateLeafAdvisory(payload: LeafAdvisoryRequest): Promise<LeafAdvisoryResponse> {
  const resp = await apiClient.post<LeafAdvisoryResponse>('/api/leaf-advisory/generate', payload);
  return resp.data;
}
