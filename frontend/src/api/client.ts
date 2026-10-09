import axios from 'axios';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
export const DB_NAME = import.meta.env.VITE_DB_NAME || 'leaf_disease_db';

export const USER_ID_KEY = 'kweka_user_id';
export const DEFAULT_USER_ID = 'usr_agronomist_01';

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

// Request interceptor to automatically inject X-User-ID header for multi-tenant isolation
apiClient.interceptors.request.use(
  (config) => {
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
