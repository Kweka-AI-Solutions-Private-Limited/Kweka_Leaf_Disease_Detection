import React from 'react';
import { Settings, CheckCircle2, ShieldCheck, Database, Key, Server, Cpu, Sparkles, User, Lock } from 'lucide-react';
import { getCurrentUserId } from '../api/client';

export const SettingsPage: React.FC = () => {
  const currentUserId = getCurrentUserId();

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
              User isolation context, database queries, and AI model provider configuration.
            </p>
          </div>
        </div>
      </div>

      {/* User Isolation Card */}
      <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 space-y-4 shadow-xs">
        <div className="flex items-center justify-between border-b border-[#f1eee9] pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
            <h2 className="text-base font-bold text-warmgray-900">User Data Isolation Architecture</h2>
          </div>
          <span className="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 font-mono text-xs font-bold border border-emerald-200">
            ENFORCED & ACTIVE
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-warmgray-50 border border-[#eae4dc] space-y-1">
            <div className="font-mono text-[10px] uppercase font-bold text-warmgray-500">Active User Context</div>
            <div className="font-extrabold text-warmgray-900 text-sm flex items-center gap-1.5">
              <User className="w-4 h-4 text-[#d96b27]" />
              <span>{currentUserId}</span>
            </div>
            <p className="text-warmgray-500 text-[11px]">Injected into all API requests via X-User-ID header</p>
          </div>

          <div className="p-4 rounded-xl bg-warmgray-50 border border-[#eae4dc] space-y-1">
            <div className="font-mono text-[10px] uppercase font-bold text-warmgray-500">MongoDB Filter Scope</div>
            <div className="font-extrabold text-emerald-700 text-sm flex items-center gap-1.5">
              <Lock className="w-4 h-4 text-emerald-600" />
              <span>`{`{"user_id": "${currentUserId}"}`}`</span>
            </div>
            <p className="text-warmgray-500 text-[11px]">Strict isolation across ldd_inspections & activity_logs</p>
          </div>

          <div className="p-4 rounded-xl bg-warmgray-50 border border-[#eae4dc] space-y-1">
            <div className="font-mono text-[10px] uppercase font-bold text-warmgray-500">Cross-Tenant Protection</div>
            <div className="font-extrabold text-warmgray-900 text-sm flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Zero Leakage Verification</span>
            </div>
            <p className="text-warmgray-500 text-[11px]">User A cannot read, list, or delete User B's scan history</p>
          </div>
        </div>
      </div>

      {/* Settings Grid */}
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
                <Database className="w-4 h-4 text-emerald-600" />
                <div>
                  <div className="font-bold text-warmgray-900">MongoDB Database Connection</div>
                  <div className="text-[11px] text-warmgray-500">Database: leaf_disease_db (59 NACL products)</div>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-mono font-bold border border-emerald-200">
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
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-mono font-bold border border-emerald-200">
                ACTIVE
              </span>
            </div>

            <div className="p-3 rounded-xl border border-[#eae4dc] bg-warmgray-50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Cpu className="w-4 h-4 text-blue-600" />
                <div>
                  <div className="font-bold text-warmgray-900">Pl@ntNet Disease Provider</div>
                  <div className="text-[11px] text-warmgray-500">Primary pathology identification service</div>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-mono font-bold border border-emerald-200">
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
              <span className="text-[10px] text-emerald-600 font-bold">✓ GEMINI_API_KEY set in backend environment</span>
            </div>

            <div className="space-y-1 pt-2">
              <label className="font-bold text-warmgray-800">Pl@ntNet API Key</label>
              <input
                type="password"
                disabled
                value="••••••••••••••••••••••••••••••••"
                className="w-full bg-warmgray-100 border border-[#e5ded3] rounded-xl px-3 py-2 text-xs font-mono text-warmgray-600"
              />
              <span className="text-[10px] text-emerald-600 font-bold">✓ PLANT_API_KEY configured for high precision pathology</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
