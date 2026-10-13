import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import {
  ShieldAlert,
  AlertCircle,
  CheckCircle2,
  Clock,
  X,
  LogIn,
  ExternalLink,
  RotateCcw
} from 'lucide-react';
import { SidebarLayout } from './components/layout/SidebarLayout';
import { DashboardPage } from './pages/DashboardPage';
import { LeafDiseasePage } from './pages/LeafDiseasePage';
import { PestDetectionPage } from './pages/PestDetectionPage';
import { UnifiedTestingPage } from './pages/UnifiedTestingPage';
import { LeafAdvisoryPage } from './pages/LeafAdvisoryPage';
import { CatalogPage } from './pages/CatalogPage';
import { HistoryPage } from './pages/HistoryPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';
import { exchangeAuthCode } from './api/auth';
import { setAuthSession } from './api/client';

export const KWEKA_LOGIN_URL = 'https://agents.kweka.ai/login';

export function App() {
  const [authenticating, setAuthenticating] = useState<boolean>(false);
  const [authBanner, setAuthBanner] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [authFailureError, setAuthFailureError] = useState<string | null>(null);

  useEffect(() => {
    // 1. Check if parent platform redirected with single-use ?exchange_code=<token>
    const params = new URLSearchParams(window.location.search);
    const exchangeCode = params.get('exchange_code');

    if (exchangeCode && exchangeCode.trim()) {
      setAuthenticating(true);
      exchangeAuthCode(exchangeCode.trim())
        .then((res) => {
          setAuthSession(res.token, res.user);
          // Strip exchange_code parameter from browser URL bar without reloading
          const cleanUrl = window.location.pathname + (window.location.hash || '');
          window.history.replaceState({}, document.title, cleanUrl);

          setAuthBanner({
            message: `Authenticated as ${res.user.name || res.user.email} (${res.user.company || 'Kweka'}). JWT session active.`,
            type: 'success',
          });
          setAuthFailureError(null);
          setTimeout(() => setAuthBanner(null), 7000);
        })
        .catch((err: any) => {
          console.error('[AUTH_ERROR] Parent exchange code verification failed:', err);
          const detail =
            err.response?.data?.detail ||
            'Exchange token verification failed or has expired. Please log in again to generate a new session.';
          setAuthFailureError(detail);
          // Clean exchange_code from URL
          const cleanUrl = window.location.pathname + (window.location.hash || '');
          window.history.replaceState({}, document.title, cleanUrl);
        })
        .finally(() => {
          setAuthenticating(false);
        });
    }

    // 2. Listen to 401 Unauthorized / Token Expired event from API client
    const handleAuthExpired = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      setAuthFailureError(
        detail?.message || 'Your authorization session has expired. Please log in again to continue.'
      );
    };

    window.addEventListener('kweka_auth_expired', handleAuthExpired);
    return () => window.removeEventListener('kweka_auth_expired', handleAuthExpired);
  }, []);

  return (
    <BrowserRouter>
      {/* ── Global Auth Banner / Toast (for successful auth) ────────────────── */}
      {authBanner && (
        <div className="fixed top-4 right-4 z-50 max-w-md animate-in slide-in-from-top duration-300">
          <div
            className={`p-4 rounded-2xl shadow-lg border flex items-start gap-3 ${
              authBanner.type === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                : 'bg-red-50 border-red-200 text-red-900'
            }`}
          >
            {authBanner.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            )}
            <div className="flex-1 text-xs">
              <div className="font-bold">
                {authBanner.type === 'success' ? 'Parent Platform Authentication' : 'Authentication Error'}
              </div>
              <div className="mt-0.5 text-xs text-warmgray-700">{authBanner.message}</div>
            </div>
            <button
              type="button"
              onClick={() => setAuthBanner(null)}
              className="p-1 rounded-lg hover:bg-black/5 text-warmgray-500"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ── Authenticating Modal Overlay (During Handshake) ─────────────────── */}
      {authenticating && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full text-center space-y-4 shadow-xl border border-[#eae4dc]">
            <div className="w-12 h-12 rounded-2xl bg-[#fdf3ed] text-[#d96b27] flex items-center justify-center mx-auto border border-[#f5d5c0]">
              <Clock className="w-6 h-6 animate-spin text-[#d96b27]" />
            </div>
            <div>
              <h3 className="font-bold text-base text-warmgray-900">Verifying Parent Exchange Code</h3>
              <p className="text-xs text-warmgray-500 mt-1">
                Validating single-use token with Kweka platform and generating your secure JWT session...
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ── Authentication Failure Screen / Modal ───────────────────────────── */}
      {authFailureError && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl max-w-md w-full p-8 shadow-2xl border border-[#eae4dc] text-center space-y-6">
            {/* Warning Icon Badge */}
            <div className="w-16 h-16 rounded-2xl bg-red-50 text-red-600 border border-red-200 flex items-center justify-center mx-auto shadow-xs">
              <ShieldAlert className="w-8 h-8 text-red-600" />
            </div>

            {/* Title & Subheading */}
            <div className="space-y-2">
              <h2 className="text-xl font-extrabold text-warmgray-900 tracking-tight">
                Authentication Failed
              </h2>
              <p className="text-xs text-warmgray-500 font-medium">
                We could not verify your session with the Kweka platform.
              </p>
            </div>

            {/* Error Detail Pill */}
            <div className="p-3.5 rounded-xl bg-red-50/80 border border-red-200 text-left space-y-1">
              <div className="text-[10px] font-mono uppercase font-bold text-red-700">Failure Reason</div>
              <div className="text-xs font-semibold text-red-900">{authFailureError}</div>
            </div>

            <p className="text-xs text-warmgray-500 leading-relaxed">
              Exchange codes are single-use and time-limited for security. Please log in again to the Kweka Parent Platform to generate a fresh authenticated session.
            </p>

            {/* Action Buttons */}
            <div className="space-y-2.5 pt-2">
              <a
                href={KWEKA_LOGIN_URL}
                className="w-full py-3 px-4 rounded-xl bg-[#d96b27] hover:bg-[#c55d1d] active:scale-[0.98] text-white text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-2 cursor-pointer no-underline"
              >
                <LogIn className="w-4 h-4" />
                <span>Log In to Kweka Platform</span>
                <ExternalLink className="w-3.5 h-3.5 ml-0.5" />
              </a>

              <button
                type="button"
                onClick={() => setAuthFailureError(null)}
                className="w-full py-2.5 px-4 rounded-xl border border-[#e5ded3] bg-white text-xs font-bold text-warmgray-600 hover:bg-warmgray-50 transition-colors cursor-pointer"
              >
                Continue as Guest / Demo Mode
              </button>
            </div>
          </div>
        </div>
      )}

      <SidebarLayout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/dashboard" element={<Navigate to="/" replace />} />
          <Route path="/scan" element={<Navigate to="/leaf-diagnosis" replace />} />
          <Route path="/leaf-disease/:runId?" element={<Navigate to="/leaf-diagnosis" replace />} />
          <Route path="/pests" element={<Navigate to="/leaf-diagnosis" replace />} />
          <Route path="/pest-detection" element={<Navigate to="/leaf-diagnosis" replace />} />
          <Route path="/leaf-diagnosis" element={<UnifiedTestingPage />} />
          <Route path="/leaf-advisory" element={<LeafAdvisoryPage />} />
          <Route path="/test-lab" element={<Navigate to="/leaf-diagnosis" replace />} />
          <Route path="/unified-test" element={<Navigate to="/leaf-diagnosis" replace />} />
          <Route path="/catalog" element={<CatalogPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </SidebarLayout>
    </BrowserRouter>
  );
}

export default App;
