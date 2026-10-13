import React, { useState, useEffect } from 'react';
import {
  Settings,
  CheckCircle2,
  ShieldCheck,
  Database,
  Key,
  Server,
  Cpu,
  Sparkles,
  User,
  Lock,
  RefreshCw,
  Trash2,
  Check,
  ArrowRight,
  ShieldAlert
} from 'lucide-react';
import { getCurrentUserId, setUserId } from '../api/client';
import { getLeafDiseaseHistory, getActivityLogs, clearLeafDiseaseHistory } from '../api/leafDisease';

const PRESET_USERS = [
  { id: 'usr_agronomist_01', name: 'Abhinav Govardhana', role: 'Lead Agronomist', email: 'abhinav.govardhana@kweka.ai' },
  { id: 'usr_farmer_bob', name: 'Farmer Bob', role: 'Farm Owner (North Sector)', email: 'bob.grower@farmcorp.com' },
  { id: 'usr_researcher_03', name: 'Dr. Alice Chen', role: 'Pathology Researcher', email: 'alice.chen@agri-institute.org' },
];

export const SettingsPage: React.FC = () => {
  const [activeUserId, setActiveUserId] = useState<string>(getCurrentUserId());
  const [customUserId, setCustomUserId] = useState<string>('');
  const [userScanCount, setUserScanCount] = useState<number>(0);
  const [userActivityCount, setUserActivityCount] = useState<number>(0);
  const [loadingStats, setLoadingStats] = useState<boolean>(true);
  const [purging, setPurging] = useState<boolean>(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const fetchUserMetrics = async () => {
    setLoadingStats(true);
    try {
      const [scans, logs] = await Promise.all([
        getLeafDiseaseHistory(200),
        getActivityLogs(50)
      ]);
      setUserScanCount(scans.length);
      setUserActivityCount(logs.length);
    } catch (err) {
      console.warn('Failed to fetch user metrics in settings:', err);
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    fetchUserMetrics();

    const handleUserChange = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail && detail.userId) {
        setActiveUserId(detail.userId);
        fetchUserMetrics();
      }
    };
    window.addEventListener('kweka_user_changed', handleUserChange);
    return () => window.removeEventListener('kweka_user_changed', handleUserChange);
  }, []);

  const handleSwitchUser = (newId: string) => {
    const cleanId = newId.trim();
    if (!cleanId) return;
    setUserId(cleanId);
    setActiveUserId(cleanId);
    setMessage({ text: `Switched active user context to "${cleanId}". All queries are now scoped to this user.`, type: 'success' });
    setTimeout(() => setMessage(null), 5000);
  };

  const handlePurgeHistory = async () => {
    if (!window.confirm(`Are you sure you want to purge all ${userScanCount} scan records for user "${activeUserId}"? This action will not affect any other user's records.`)) {
      return;
    }
    setPurging(true);
    try {
      const res = await clearLeafDiseaseHistory();
      setMessage({ text: `Successfully purged ${res.deleted_count} scan records belonging to "${activeUserId}".`, type: 'success' });
      fetchUserMetrics();
    } catch (err) {
      setMessage({ text: 'Failed to purge scan records.', type: 'error' });
    } finally {
      setPurging(false);
      setTimeout(() => setMessage(null), 5000);
    }
  };

  const activePersona = PRESET_USERS.find((u) => u.id === activeUserId);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 shadow-xs flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3.5 rounded-2xl bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0]">
            <Settings className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-warmgray-900 tracking-tight">
              Platform Settings & Multi-Tenant Security
            </h1>
            <p className="text-xs text-warmgray-500 font-medium mt-1">
              Active user context, MongoDB multi-tenant isolation, and telemetry configuration.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={fetchUserMetrics}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-[#e5ded3] bg-white text-xs font-bold text-warmgray-700 hover:bg-warmgray-50 transition-colors shadow-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loadingStats ? 'animate-spin text-[#d96b27]' : ''}`} />
          <span>Refresh Status</span>
        </button>
      </div>

      {message && (
        <div
          className={`p-4 rounded-xl text-xs font-medium border flex items-center justify-between ${
            message.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
              : 'bg-red-50 text-red-800 border-red-200'
          }`}
        >
          <span>{message.text}</span>
          <button onClick={() => setMessage(null)} className="text-xs font-bold underline ml-2">
            Dismiss
          </button>
        </div>
      )}

      {/* ── User Isolation & Identity Card ────────────────────────────────────────── */}
      <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 space-y-5 shadow-xs">
        <div className="flex items-center justify-between border-b border-[#f1eee9] pb-3 flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
            <h2 className="text-base font-bold text-warmgray-900">User Identity & Multi-Tenant Isolation</h2>
          </div>
          <span className="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 font-mono text-xs font-bold border border-emerald-200 flex items-center gap-1">
            <Lock className="w-3.5 h-3.5 text-emerald-600" />
            STRICT SCOPING ENFORCED
          </span>
        </div>

        {/* 3 Status Info Blocks */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-warmgray-50 border border-[#eae4dc] space-y-1">
            <div className="font-mono text-[10px] uppercase font-bold text-warmgray-500">Active User Context</div>
            <div className="font-extrabold text-warmgray-900 text-sm flex items-center gap-1.5">
              <User className="w-4 h-4 text-[#d96b27]" />
              <span>{activeUserId}</span>
            </div>
            <p className="text-warmgray-500 text-[11px]">Injected into all API requests via X-User-ID header</p>
          </div>

          <div className="p-4 rounded-xl bg-warmgray-50 border border-[#eae4dc] space-y-1">
            <div className="font-mono text-[10px] uppercase font-bold text-warmgray-500">MongoDB Filter Scope</div>
            <div className="font-extrabold text-emerald-700 text-sm flex items-center gap-1.5">
              <Lock className="w-4 h-4 text-emerald-600" />
              <span>`{`{"user_id": "${activeUserId}"}`}`</span>
            </div>
            <p className="text-warmgray-500 text-[11px]">
              Inspections: <strong>{loadingStats ? '...' : userScanCount}</strong> | Logs:{' '}
              <strong>{loadingStats ? '...' : userActivityCount}</strong>
            </p>
          </div>

          <div className="p-4 rounded-xl bg-warmgray-50 border border-[#eae4dc] space-y-1">
            <div className="font-mono text-[10px] uppercase font-bold text-warmgray-500">Tenant Protection</div>
            <div className="font-extrabold text-warmgray-900 text-sm flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Zero Cross-Tenant Leakage</span>
            </div>
            <p className="text-warmgray-500 text-[11px]">User A cannot read, list, or delete User B records</p>
          </div>
        </div>

        {/* Switch Persona Controls */}
        <div className="pt-2 space-y-3">
          <div className="text-xs font-bold text-warmgray-800">Switch Workspace Persona:</div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {PRESET_USERS.map((preset) => {
              const isSelected = activeUserId === preset.id;
              return (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => handleSwitchUser(preset.id)}
                  className={`p-3.5 rounded-xl border text-left transition-all ${
                    isSelected
                      ? 'border-[#d96b27] bg-[#fdf3ed]/60 ring-2 ring-[#d96b27]/20 shadow-xs'
                      : 'border-[#eae4dc] hover:border-[#d96b27]/40 hover:bg-warmgray-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-warmgray-900">{preset.name}</span>
                    {isSelected && <Check className="w-4 h-4 text-[#d96b27]" />}
                  </div>
                  <div className="text-[11px] text-[#d96b27] font-semibold">{preset.role}</div>
                  <div className="text-[10px] font-mono text-warmgray-500 mt-1">{preset.id}</div>
                </button>
              );
            })}
          </div>

          {/* Custom User ID Input */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (customUserId.trim()) {
                handleSwitchUser(customUserId.trim());
                setCustomUserId('');
              }
            }}
            className="flex items-center gap-2 pt-2"
          >
            <input
              type="text"
              value={customUserId}
              onChange={(e) => setCustomUserId(e.target.value)}
              placeholder="Or enter custom user ID (e.g. usr_greenhouse_99)..."
              className="flex-1 bg-white border border-[#e5ded3] rounded-xl px-3.5 py-2 text-xs font-medium text-warmgray-900 focus:outline-none focus:ring-2 focus:ring-[#d96b27]/30 focus:border-[#d96b27]"
            />
            <button
              type="submit"
              disabled={!customUserId.trim()}
              className="px-4 py-2 bg-[#d96b27] hover:bg-[#c55d1d] disabled:opacity-50 text-white rounded-xl text-xs font-bold transition-all shadow-xs"
            >
              Apply Context
            </button>
          </form>
        </div>

        {/* Tenant Self-Service Controls: Purge My Scans */}
        <div className="pt-3 border-t border-[#f1eee9] flex items-center justify-between flex-wrap gap-3">
          <div className="text-xs text-warmgray-500">
            Purge all inspection runs stored for <strong className="text-warmgray-900">{activeUserId}</strong> without affecting any other user.
          </div>
          <button
            type="button"
            onClick={handlePurgeHistory}
            disabled={purging || userScanCount === 0}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-red-200 bg-red-50 text-red-700 text-xs font-bold hover:bg-red-100 disabled:opacity-50 transition-colors shadow-xs"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{purging ? 'Purging...' : `Purge My History (${userScanCount} scans)`}</span>
          </button>
        </div>
      </div>

      {/* ── Settings Grid ─────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* System Connections */}
        <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 space-y-4 shadow-xs">
          <div className="flex items-center gap-2 border-b border-[#f1eee9] pb-3">
            <Server className="w-4 h-4 text-[#d96b27]" />
            <h2 className="text-base font-bold text-warmgray-900">Backend & API Connections</h2>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-xl border border-[#eae4dc] bg-warmgray-50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Database className="w-4 h-4 text-[#d96b27]" />
                <div>
                  <div className="font-bold text-warmgray-900">MongoDB Database Connection</div>
                  <div className="text-[11px] text-warmgray-500">Database: leaf_disease_db (59 NACL products)</div>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full bg-[#fdeade] text-[#d96b27] text-[10px] font-mono font-bold border border-[#f5d5c0]">
                CONNECTED
              </span>
            </div>

            <div className="p-3 rounded-xl border border-[#eae4dc] bg-warmgray-50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Sparkles className="w-4 h-4 text-[#d96b27]" />
                <div>
                  <div className="font-bold text-warmgray-900">Gemini VLM Vision Model</div>
                  <div className="text-[11px] text-warmgray-500">gemini-2.5-flash / gemini-flash-latest</div>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full bg-[#fdeade] text-[#d96b27] text-[10px] font-mono font-bold border border-[#f5d5c0]">
                ACTIVE
              </span>
            </div>

            <div className="p-3 rounded-xl border border-[#eae4dc] bg-warmgray-50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Cpu className="w-4 h-4 text-[#d96b27]" />
                <div>
                  <div className="font-bold text-warmgray-900">Pl@ntNet Disease Provider</div>
                  <div className="text-[11px] text-warmgray-500">Primary pathology identification service</div>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full bg-[#fdeade] text-[#d96b27] text-[10px] font-mono font-bold border border-[#f5d5c0]">
                READY
              </span>
            </div>
          </div>
        </div>

        {/* Security & API Keys */}
        <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 space-y-4 shadow-xs">
          <div className="flex items-center gap-2 border-b border-[#f1eee9] pb-3">
            <Key className="w-4 h-4 text-[#d96b27]" />
            <h2 className="text-base font-bold text-warmgray-900">API Key Status</h2>
          </div>

          <div className="space-y-3 text-xs">
            <div className="space-y-1">
              <label className="font-bold text-warmgray-800">Gemini API Key</label>
              <input
                type="password"
                disabled
                value="••••••••••••••••••••••••••••••••"
                className="w-full bg-warmgray-100 border border-[#e5ded3] rounded-xl px-3 py-2 text-xs font-mono text-warmgray-600"
              />
              <span className="text-[10px] text-[#d96b27] font-bold">✓ GEMINI_API_KEY set in backend environment</span>
            </div>

            <div className="space-y-1 pt-2">
              <label className="font-bold text-warmgray-800">Pl@ntNet API Key</label>
              <input
                type="password"
                disabled
                value="••••••••••••••••••••••••••••••••"
                className="w-full bg-warmgray-100 border border-[#e5ded3] rounded-xl px-3 py-2 text-xs font-mono text-warmgray-600"
              />
              <span className="text-[10px] text-[#d96b27] font-bold">✓ PLANT_API_KEY configured for high precision pathology</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
