import { apiClient } from './client';

export interface UserProfile {
  id: string;
  email?: string | null;
  name: string;
  first_name?: string | null;
  last_name?: string | null;
  company?: string | null;
  job_title?: string | null;
  mobile_number?: string | null;
  role: string;
  is_active: boolean;
}

export interface AuthExchangeResponse {
  token: string;
  token_type: string;
  expires_in_days: number;
  user: UserProfile;
}

/**
 * Exchanges a single-use exchange_code from Kweka parent platform for a verified JWT token.
 */
export async function exchangeAuthCode(exchangeCode: string): Promise<AuthExchangeResponse> {
  const response = await apiClient.post<AuthExchangeResponse>('/api/auth/exchange', {
    exchange_code: exchangeCode.trim(),
  });
  return response.data;
}

/**
 * Validates active Bearer JWT token and returns verified user profile.
 */
export async function fetchCurrentUserProfile(): Promise<UserProfile> {
  const response = await apiClient.get<UserProfile>('/api/auth/me');
  return response.data;
}
