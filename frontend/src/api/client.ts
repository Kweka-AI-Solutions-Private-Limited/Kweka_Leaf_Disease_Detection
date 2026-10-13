import axios from 'axios';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
export const DB_NAME = import.meta.env.VITE_DB_NAME || 'leaf_disease_db';

export const AUTH_TOKEN_KEY = 'kweka_auth_token';
export const USER_PROFILE_KEY = 'kweka_user_profile';
export const USER_ID_KEY = 'kweka_user_id';
export const DEFAULT_USER_ID = 'usr_agronomist_01';

/**
 * Returns stored JWT access token, or null if unauthenticated.
 */
export function getAuthToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Returns parsed user profile claims if stored.
 */
export function getCurrentUserProfile(): any | null {
  try {
    const raw = localStorage.getItem(USER_PROFILE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/**
 * Sets the verified JWT token and User Profile in localStorage and dispatches a global event.
 */
export function setAuthSession(token: string, user: any): void {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
  localStorage.setItem(USER_PROFILE_KEY, JSON.stringify(user));
  const userId = user.id || user._id || user.email || DEFAULT_USER_ID;
  localStorage.setItem(USER_ID_KEY, userId);
  window.dispatchEvent(
    new CustomEvent('kweka_user_changed', { detail: { userId, user, token } })
  );
}

/**
 * Clears active JWT session and resets to guest/default persona.
 */
export function clearAuthSession(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(USER_PROFILE_KEY);
  localStorage.removeItem(USER_ID_KEY);
  window.dispatchEvent(
    new CustomEvent('kweka_user_changed', { detail: { userId: DEFAULT_USER_ID, user: null } })
  );
}

/**
 * Returns the active isolated User ID from localStorage, initializing a default if unassigned.
 */
export function getCurrentUserId(): string {
  let userId = localStorage.getItem(USER_ID_KEY);
  if (!userId || !userId.trim()) {
    userId = DEFAULT_USER_ID;
    localStorage.setItem(USER_ID_KEY, userId);
  }
  return userId;
}

/**
 * Sets the active User ID in localStorage and dispatches a global event to notify UI components.
 */
export function setUserId(newUserId: string): void {
  const cleanId = newUserId.trim() || DEFAULT_USER_ID;
  localStorage.setItem(USER_ID_KEY, cleanId);
  window.dispatchEvent(new CustomEvent('kweka_user_changed', { detail: { userId: cleanId } }));
}

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000,
});

// Request interceptor: injects Authorization Bearer JWT & X-User-ID headers
apiClient.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    config.headers['X-User-ID'] = getCurrentUserId();
    return config;
  },
  (error) => Promise.reject(error)
);

// Automatic retry interceptor for handling Cloud Run cold starts and transient 502/503/504 errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    if (!config) return Promise.reject(error);

    config.__retryCount = config.__retryCount || 0;
    const MAX_RETRIES = 3;

    const isRetryable =
      !error.response ||
      error.response.status === 503 ||
      error.response.status === 502 ||
      error.response.status === 504;

    if (isRetryable && config.__retryCount < MAX_RETRIES) {
      config.__retryCount += 1;
      const delayMs = config.__retryCount * 1500;
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      return apiClient(config);
    }

    if (error.response?.status === 401 && !config.url?.includes('/api/auth/exchange')) {
      clearAuthSession();
      window.dispatchEvent(
        new CustomEvent('kweka_auth_expired', {
          detail: {
            message:
              error.response?.data?.detail ||
              'Your session authorization has expired or is invalid. Please log in again to continue.',
          },
        })
      );
    }

    return Promise.reject(error);
  }
);

export function getStorageUrl(path?: string | null): string {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  return `${BASE_URL}/${cleanPath}`;
}
