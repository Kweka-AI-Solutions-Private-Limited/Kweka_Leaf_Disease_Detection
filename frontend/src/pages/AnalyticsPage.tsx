import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3,
  TrendingUp,
  Sprout,
  ShieldCheck,
  Sparkles,
  CheckCircle2,
  PieChart,
  User,
  Lock,
  RefreshCw,
  Clock,
  Bug,
  Activity,
  ArrowRight
} from 'lucide-react';
import { getCurrentUserId } from '../api/client';
import { getLeafDiseaseHistory, getNaclCatalog, LeafDiseaseAnalysisResponse } from '../api/leafDisease';

const PRESET_USER_MAP: Record<string, string> = {
  usr_agronomist_01: 'Abhinav Govardhana (Lead Agronomist)',
  usr_farmer_bob: 'Farmer Bob (Farm Owner)',
  usr_researcher_03: 'Dr. Alice Chen (Pathology Researcher)',
};

export const AnalyticsPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeUserId, setActiveUserId] = useState<string>(getCurrentUserId());
  const [scans, setScans] = useState<LeafDiseaseAnalysisResponse[]>([]);
  const [catalogCount, setCatalogCount] = useState<number>(59);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const historyData = await getLeafDiseaseHistory(200);
      setScans(historyData);

      try {
        const catRes = await getNaclCatalog();
        setCatalogCount(catRes.total_count || 59);
      } catch {
        setCatalogCount(59);
      }
    } catch (err) {
      console.warn('Failed to load user analytics data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    const handleUserChange = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail && detail.userId) {
        setActiveUserId(detail.userId);
        loadData();
      }
    };
    window.addEventListener('kweka_user_changed', handleUserChange);
    return () => window.removeEventListener('kweka_user_changed', handleUserChange);
  }, []);

  const currentUserName = PRESET_USER_MAP[activeUserId] || activeUserId;

  // Dynamic user-isolated computations
  const totalScans = scans.length;
  const successScans = scans.filter((s) => s.status === 'SUCCESS').length;
  const uncertainScans = scans.filter((s) => s.status === 'UNCERTAIN').length;
  const failedScans = scans.filter((s) => s.status === 'FAILED').length;
  const successRate = totalScans > 0 ? ((successScans / totalScans) * 100).toFixed(1) : '100.0';

  // Dynamic Crop Frequency Aggregation
  const cropCounts: Record<string, number> = {};
  scans.forEach((s) => {
    const cName = s.crop?.crop_name;
    if (cName && cName.trim() && cName !== 'Unknown') {
      cropCounts[cName] = (cropCounts[cName] || 0) + 1;
    }
  });

  const topCrops = Object.entries(cropCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const uniqueCropCount = Object.keys(cropCounts).length;

  // Dynamic Pathology Category Breakdown
  let fungalCount = 0;
  let pestCount = 0;
  let healthyCount = 0;
  let uncertainCatCount = 0;

  scans.forEach((s) => {
    const dis = (s.disease?.disease_name || '').toLowerCase();
    const pest = (s.pest?.primary_pest || '').toLowerCase();

    if (pest && !pest.includes('no pest') && !pest.includes('none') && pest !== 'unknown pest') {
      pestCount++;
    } else if (dis.includes('healthy') || dis.includes('no disease') || dis.includes('no pathology')) {
      healthyCount++;
    } else if (dis && !dis.includes('none') && !dis.includes('unknown')) {
      fungalCount++;
    } else {
      uncertainCatCount++;
    }
  });

  const catTotal = totalScans > 0 ? totalScans : 1;
  const fungalPct = Math.round((fungalCount / catTotal) * 100);
  const pestPct = Math.round((pestCount / catTotal) * 100);
  const healthyPct = Math.round((healthyCount / catTotal) * 100);
  const uncertainPct = Math.max(0, 100 - (fungalPct + pestPct + healthyPct));

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* ── Top Header Banner with Active User Identity ────────────────────────────── */}
      <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 shadow-xs flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3.5 rounded-2xl bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0]">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-extrabold text-warmgray-900 tracking-tight">
                User Telemetry & Pathology Analytics
              </h1>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-mono font-bold border border-emerald-200 flex items-center gap-1">
                <Lock className="w-3 h-3 text-emerald-600" />
                User-Isolated
              </span>
            </div>
            <p className="text-xs text-warmgray-500 font-medium mt-1 flex items-center gap-1.5 flex-wrap">
              <span>Telemetry scoped to workspace:</span>
              <strong className="text-warmgray-900 font-bold bg-warmgray-100 px-2 py-0.5 rounded-md flex items-center gap-1">
                <User className="w-3 h-3 text-[#d96b27]" />
                {currentUserName}
              </strong>
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={loadData}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-[#e5ded3] bg-white text-xs font-bold text-warmgray-700 hover:bg-warmgray-50 transition-colors shadow-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#d96b27]' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* ── Dynamic Metrics Cards Row ────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Total Inspections */}
        <div className="bg-white border border-[#eae4dc] rounded-2xl p-5 space-y-2 shadow-xs hover:border-[#d96b27]/30 transition-all">
          <div className="text-xs font-bold font-mono text-warmgray-500 uppercase flex items-center justify-between">
            <span>Total Analyses</span>
            <Sprout className="w-4 h-4 text-[#d96b27]" />
          </div>
          <div className="text-3xl font-extrabold text-warmgray-900">
            {loading ? '...' : totalScans}
          </div>
          <p className="text-xs text-warmgray-500 font-medium">
            Scans authored by <span className="font-mono font-semibold">{activeUserId}</span>
          </p>
        </div>

        {/* Metric 2: Diagnostic Certainty Rate */}
        <div className="bg-white border border-[#eae4dc] rounded-2xl p-5 space-y-2 shadow-xs hover:border-[#d96b27]/30 transition-all">
          <div className="text-xs font-bold font-mono text-warmgray-500 uppercase flex items-center justify-between">
            <span>Certainty Rate</span>
            <TrendingUp className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-3xl font-extrabold text-warmgray-900">
            {loading ? '...' : `${successRate}%`}
          </div>
          <p className="text-xs text-emerald-700 font-semibold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{successScans} confirmed / {totalScans} total</span>
          </p>
        </div>

        {/* Metric 3: Unique Host Crops */}
        <div className="bg-white border border-[#eae4dc] rounded-2xl p-5 space-y-2 shadow-xs hover:border-[#d96b27]/30 transition-all">
          <div className="text-xs font-bold font-mono text-warmgray-500 uppercase flex items-center justify-between">
            <span>Unique Crops</span>
            <Activity className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-3xl font-extrabold text-warmgray-900">
            {loading ? '...' : uniqueCropCount}
          </div>
          <p className="text-xs text-warmgray-500 font-medium">Distinct agricultural species tested</p>
        </div>

        {/* Metric 4: NACL Product Matching */}
        <div className="bg-white border border-[#eae4dc] rounded-2xl p-5 space-y-2 shadow-xs hover:border-[#d96b27]/30 transition-all">
          <div className="text-xs font-bold font-mono text-warmgray-500 uppercase flex items-center justify-between">
            <span>NACL Catalog Items</span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-3xl font-extrabold text-warmgray-900">
            {catalogCount}
          </div>
          <p className="text-xs text-warmgray-500 font-medium">Active agrochemicals index</p>
        </div>
      </div>

      {/* ── Dynamic Analytics Breakdown Grid ───────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Card 1: Dynamic Pathology Breakdown */}
        <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 space-y-4 shadow-xs">
          <div className="flex items-center justify-between border-b border-[#f1eee9] pb-3">
            <div className="flex items-center gap-2">
              <PieChart className="w-4 h-4 text-[#d96b27]" />
              <h2 className="text-base font-bold text-warmgray-900">Pathology Distribution</h2>
            </div>
            <span className="text-[11px] font-mono text-warmgray-500">Live Breakdown</span>
          </div>

          {loading ? (
            <div className="py-8 text-center text-xs font-mono text-warmgray-400">Computing telemetry...</div>
          ) : totalScans === 0 ? (
            <div className="py-10 text-center space-y-2">
              <div className="text-xs font-medium text-warmgray-500">No scans logged for this user yet.</div>
              <button
                type="button"
                onClick={() => navigate('/leaf-diagnosis')}
                className="text-xs font-bold text-[#d96b27] hover:underline"
              >
                Run first diagnosis →
              </button>
            </div>
          ) : (
            <div className="space-y-3.5">
              {[
                { label: 'Foliar Fungal / Bacterial Pathology', count: fungalCount, pct: `${fungalPct}%`, color: 'bg-[#d96b27]' },
                { label: 'Insect Pest Infestations', count: pestCount, pct: `${pestPct}%`, color: 'bg-rose-600' },
                { label: 'Healthy / Asymptomatic Foliage', count: healthyCount, pct: `${healthyPct}%`, color: 'bg-emerald-600' },
                { label: 'Uncertain / Ambiguous Specimens', count: uncertainCatCount, pct: `${uncertainPct}%`, color: 'bg-amber-500' },
              ].map((cat, i) => (
                <div key={i} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold text-warmgray-800">
                    <span>{cat.label}</span>
                    <span className="font-mono text-warmgray-600">
                      {cat.count} ({cat.pct})
                    </span>
                  </div>
                  <div className="w-full bg-warmgray-100 rounded-full h-2.5 overflow-hidden">
                    <div className={`h-full ${cat.color} transition-all duration-500`} style={{ width: cat.pct }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Card 2: Top Diagnosed Crops */}
        <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 space-y-4 shadow-xs">
          <div className="flex items-center justify-between border-b border-[#f1eee9] pb-3">
            <div className="flex items-center gap-2">
              <Sprout className="w-4 h-4 text-[#d96b27]" />
              <h2 className="text-base font-bold text-warmgray-900">Most Diagnosed Crops</h2>
            </div>
            <span className="text-[11px] font-mono text-warmgray-500">Ranked by volume</span>
          </div>

          {loading ? (
            <div className="py-8 text-center text-xs font-mono text-warmgray-400">Loading crops...</div>
          ) : topCrops.length === 0 ? (
            <div className="py-10 text-center space-y-2">
              <div className="text-xs font-medium text-warmgray-500">No crop diagnosis history recorded.</div>
              <button
                type="button"
                onClick={() => navigate('/leaf-diagnosis')}
                className="text-xs font-bold text-[#d96b27] hover:underline"
              >
                Scan a leaf now →
              </button>
            </div>
          ) : (
            <div className="space-y-3 divide-y divide-[#f5f1ea]">
              {topCrops.map(([cName, count], idx) => (
                <div key={idx} className="pt-2.5 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-warmgray-100 text-warmgray-600 font-mono text-[10px] font-bold flex items-center justify-center">
                      {idx + 1}
                    </span>
                    <span className="font-bold text-warmgray-900">{cName}</span>
                  </div>
                  <span className="font-mono font-bold text-[#d96b27] px-2.5 py-0.5 rounded-full bg-[#fdf3ed]">
                    {count} {count === 1 ? 'scan' : 'scans'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
