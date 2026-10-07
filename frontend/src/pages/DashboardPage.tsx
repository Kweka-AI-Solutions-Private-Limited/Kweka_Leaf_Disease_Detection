import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sprout,
  Building2,
  ShieldCheck,
  Sparkles,
  ArrowUpRight,
  Plus,
  History,
  BookOpen,
  BarChart3,
  Clock,
  Zap,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Database
} from 'lucide-react';
import {
  getLeafDiseaseHistory,
  getNaclCatalog,
  getActivityLogs,
  LeafDiseaseAnalysisResponse,
  ActivityLogEntry
} from '../api/leafDisease';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [recentScans, setRecentScans] = useState<LeafDiseaseAnalysisResponse[]>([]);
  const [totalScans, setTotalScans] = useState<number>(0);
  const [catalogCount, setCatalogCount] = useState<number>(0);
  const [activityLogs, setActivityLogs] = useState<ActivityLogEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Fetch scan history from ldd_inspections
      const historyData = await getLeafDiseaseHistory(200);
      setRecentScans(historyData.slice(0, 5));
      setTotalScans(historyData.length);

      // Fetch product catalog count from ldd_nacl_products
      try {
        const catRes = await getNaclCatalog();
        setCatalogCount(catRes.total_count || 59);
      } catch {
        setCatalogCount(59);
      }

      // Fetch activity logs from activity_logs collection
      try {
        const logs = await getActivityLogs(10);
        setActivityLogs(logs);
      } catch (e) {
        console.warn('Activity log fetch fallback:', e);
      }

    } catch (err) {
      console.warn('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Calculate unique crop count from actual history
  const uniqueCropsCount = new Set(
    recentScans.map((s) => s.crop?.crop_name).filter(Boolean)
  ).size;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* ── Top Header & Greeting ────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-warmgray-900 tracking-tight flex items-center gap-3">
            <span>Leaf Pathology Dashboard</span>
            <span className="text-2xl">🌿</span>
          </h1>
          <p className="text-sm font-medium text-warmgray-500 mt-1">
            Real-time analytics across your Leaf Pathology & Agrochemical AI workspace.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={loadDashboardData}
            className="px-4 py-2 bg-white border border-[#e5ded3] rounded-xl text-xs font-bold text-warmgray-700 hover:bg-warmgray-50 transition-colors shadow-xs"
          >
            Refresh
          </button>
          <button
            type="button"
            onClick={() => navigate('/scan')}
            className="flex items-center gap-2 bg-[#d96b27] hover:bg-[#c55d1d] active:scale-[0.98] text-white px-4 py-2 rounded-xl text-xs font-bold shadow-sm transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Create scan</span>
          </button>
        </div>
      </div>

      {/* ── Stat Cards Grid (4 Columns) ─────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Stat 1: Total Analyses */}
        <div className="bg-white border border-[#eae4dc] rounded-2xl p-5 space-y-3 shadow-xs hover:border-[#d96b27]/30 transition-all">
          <div className="flex items-center justify-between text-warmgray-400">
            <span className="text-xs font-bold uppercase tracking-wider font-mono text-warmgray-500">
              Total Analyses
            </span>
            <Sprout className="w-4 h-4 text-[#d96b27]" />
          </div>
          <div className="space-y-1">
            <div className="text-3xl font-extrabold text-warmgray-900">
              {loading ? '...' : totalScans}
            </div>
            <div className="text-xs text-warmgray-500 font-medium">Completed leaf scans in database</div>
          </div>
        </div>

        {/* Stat 2: Crops Diagnosed */}
        <div className="bg-white border border-[#eae4dc] rounded-2xl p-5 space-y-3 shadow-xs hover:border-[#d96b27]/30 transition-all">
          <div className="flex items-center justify-between text-warmgray-400">
            <span className="text-xs font-bold uppercase tracking-wider font-mono text-warmgray-500">
              Crops Diagnosed
            </span>
            <Building2 className="w-4 h-4 text-warmgray-400" />
          </div>
          <div className="space-y-1">
            <div className="text-3xl font-extrabold text-warmgray-900">
              {loading ? '...' : uniqueCropsCount > 0 ? uniqueCropsCount : '—'}
            </div>
            <div className="text-xs text-warmgray-500 font-medium">Unique crop species analyzed</div>
          </div>
        </div>

        {/* Stat 3: NACL Catalog */}
        <div className="bg-white border border-[#eae4dc] rounded-2xl p-5 space-y-3 shadow-xs hover:border-[#d96b27]/30 transition-all">
          <div className="flex items-center justify-between text-warmgray-400">
            <span className="text-xs font-bold uppercase tracking-wider font-mono text-warmgray-500">
              NACL Catalog
            </span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="space-y-1">
            <div className="text-3xl font-extrabold text-warmgray-900">
              {catalogCount}
            </div>
            <div className="text-xs text-warmgray-500 font-medium">Indexed agrochemical products</div>
          </div>
        </div>

        {/* Stat 4: AI Precision */}
        <div className="bg-white border border-[#eae4dc] rounded-2xl p-5 space-y-3 shadow-xs hover:border-[#d96b27]/30 transition-all">
          <div className="flex items-center justify-between text-warmgray-400">
            <span className="text-xs font-bold uppercase tracking-wider font-mono text-warmgray-500">
              AI System Status
            </span>
            <Sparkles className="w-4 h-4 text-amber-500" />
          </div>
          <div className="space-y-1">
            <div className="text-3xl font-extrabold text-emerald-600 flex items-center gap-1.5 text-2xl">
              <CheckCircle2 className="w-6 h-6 text-emerald-600" />
              <span>Active</span>
            </div>
            <div className="text-xs text-warmgray-500 font-medium">FastAPI + Gemini Vision fallback</div>
          </div>
        </div>
      </div>

      {/* ── Main Dashboard Content Grid (2 Columns: 8 cols left, 4 cols right) ─────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Recent Scans */}
        <div className="lg:col-span-8 space-y-6">
          <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 space-y-4 shadow-xs">
            <div className="flex items-center justify-between border-b border-[#f1eee9] pb-4">
              <div className="flex items-center gap-2">
                <Sprout className="w-4 h-4 text-[#d96b27]" />
                <h2 className="text-base font-bold text-warmgray-900">Recent Analyses ({totalScans})</h2>
              </div>
              <button
                type="button"
                onClick={() => navigate('/history')}
                className="text-xs font-bold text-[#d96b27] hover:text-[#b85119] flex items-center gap-1 transition-colors"
              >
                <span>View all</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {loading ? (
              <div className="py-8 text-center text-xs font-mono text-warmgray-400">
                Loading recent scan history...
              </div>
            ) : recentScans.length === 0 ? (
              <div className="py-10 text-center space-y-3">
                <div className="w-12 h-12 rounded-full bg-[#fdeade] text-[#d96b27] flex items-center justify-center mx-auto">
                  <Sprout className="w-6 h-6" />
                </div>
                <div className="text-sm font-bold text-warmgray-800">No scans executed yet</div>
                <p className="text-xs text-warmgray-500 max-w-sm mx-auto">
                  Upload a leaf photograph to test real-time Pl@ntNet species identification and NACL treatment advisory.
                </p>
                <button
                  type="button"
                  onClick={() => navigate('/scan')}
                  className="px-4 py-2 rounded-xl bg-[#d96b27] text-white text-xs font-bold shadow-xs hover:bg-[#c55d1d] transition-colors"
                >
                  Start First Scan
                </button>
              </div>
            ) : (
              <div className="divide-y divide-[#f5f1ea]">
                {recentScans.map((scan) => (
                  <div
                    key={scan.analysis_id}
                    onClick={() => navigate('/scan')}
                    className="py-3.5 flex items-center justify-between gap-4 hover:bg-warmgray-50 px-3 rounded-xl transition-colors cursor-pointer group"
                  >
                    <div className="flex items-center gap-3.5 min-w-0">
                      <div className="w-9 h-9 rounded-xl bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0] flex items-center justify-center shrink-0">
                        <Sprout className="w-5 h-5" />
                      </div>
                      <div className="min-w-0 space-y-0.5">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-sm text-warmgray-900 group-hover:text-[#d96b27] transition-colors truncate">
                            {scan.crop?.crop_name || 'Foliage'}
                          </span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-[#fdf3ed] text-[#d96b27]">
                            {scan.disease?.disease_name ? scan.disease.disease_name.split('(')[0] : 'Diagnosed'}
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ${
                              scan.status === 'SUCCESS'
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : scan.status === 'UNCERTAIN'
                                ? 'bg-amber-50 text-amber-700 border border-amber-200'
                                : 'bg-red-50 text-red-700 border border-red-200'
                            }`}
                          >
                            {scan.status}
                          </span>
                        </div>
                        <div className="text-xs text-warmgray-500 font-mono truncate">
                          ID: {scan.analysis_id} • {new Date(scan.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>

                    <button
                      type="button"
                      className="px-3 py-1.5 rounded-lg border border-[#e5ded3] bg-white text-xs font-bold text-warmgray-700 hover:border-[#d96b27] hover:text-[#d96b27] transition-colors shrink-0"
                    >
                      View
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Quick Actions */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 space-y-4 shadow-xs">
            <div className="flex items-center gap-2 border-b border-[#f1eee9] pb-3">
              <Zap className="w-4 h-4 text-[#d96b27]" />
              <h2 className="text-base font-bold text-warmgray-900">Quick actions</h2>
            </div>

            <div className="space-y-2">
              <button
                type="button"
                onClick={() => navigate('/scan')}
                className="w-full p-3 rounded-xl border border-[#eae4dc] hover:border-[#d96b27] hover:bg-[#fdf3ed]/50 flex items-center justify-between text-left group transition-all"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-[#fdf3ed] text-[#d96b27]">
                    <Sprout className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-bold text-warmgray-800 group-hover:text-[#d96b27]">
                    Diagnose Leaf Pathology
                  </span>
                </div>
                <ArrowUpRight className="w-4 h-4 text-warmgray-400 group-hover:text-[#d96b27]" />
              </button>

              <button
                type="button"
                onClick={() => navigate('/catalog')}
                className="w-full p-3 rounded-xl border border-[#eae4dc] hover:border-[#d96b27] hover:bg-[#fdf3ed]/50 flex items-center justify-between text-left group transition-all"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700">
                    <BookOpen className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-bold text-warmgray-800 group-hover:text-[#d96b27]">
                    Browse NACL Catalog ({catalogCount})
                  </span>
                </div>
                <ArrowUpRight className="w-4 h-4 text-warmgray-400 group-hover:text-[#d96b27]" />
              </button>

              <button
                type="button"
                onClick={() => navigate('/history')}
                className="w-full p-3 rounded-xl border border-[#eae4dc] hover:border-[#d96b27] hover:bg-[#fdf3ed]/50 flex items-center justify-between text-left group transition-all"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-50 text-blue-700">
                    <History className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-bold text-warmgray-800 group-hover:text-[#d96b27]">
                    View Scan History
                  </span>
                </div>
                <ArrowUpRight className="w-4 h-4 text-warmgray-400 group-hover:text-[#d96b27]" />
              </button>

              <button
                type="button"
                onClick={() => navigate('/analytics')}
                className="w-full p-3 rounded-xl border border-[#eae4dc] hover:border-[#d96b27] hover:bg-[#fdf3ed]/50 flex items-center justify-between text-left group transition-all"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-purple-50 text-purple-700">
                    <BarChart3 className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-bold text-warmgray-800 group-hover:text-[#d96b27]">
                    View Analytics & Insights
                  </span>
                </div>
                <ArrowUpRight className="w-4 h-4 text-warmgray-400 group-hover:text-[#d96b27]" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom Section: Live System Activity Log Stream (from activity_logs collection) ──────────────────────── */}
      <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 space-y-4 shadow-xs">
        <div className="flex items-center justify-between border-b border-[#f1eee9] pb-4">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#d96b27]" />
            <h2 className="text-base font-bold text-warmgray-900">Live Activity Stream (`activity_logs`)</h2>
          </div>
          <span className="text-xs font-mono font-semibold text-warmgray-500 bg-warmgray-100 px-2.5 py-1 rounded-lg">
            {activityLogs.length} events logged
          </span>
        </div>

        {activityLogs.length === 0 ? (
          <div className="py-6 text-center text-xs text-warmgray-500 font-mono">
            No activities recorded in `activity_logs` yet. Run a leaf scan or catalog operation to generate activity logs.
          </div>
        ) : (
          <div className="space-y-3">
            {activityLogs.map((log, idx) => (
              <div key={log.id || log._id || idx} className="flex items-start gap-4 text-xs hover:bg-warmgray-50 p-2.5 rounded-xl transition-colors">
                <div className={`p-2 rounded-xl shrink-0 mt-0.5 ${
                  log.status === 'SUCCESS' ? 'bg-emerald-50 text-emerald-700' :
                  log.status === 'FAILED' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'
                }`}>
                  {log.category === 'DIAGNOSIS' ? <Sprout className="w-4 h-4" /> :
                   log.category === 'CATALOG' ? <ShieldCheck className="w-4 h-4" /> :
                   <Database className="w-4 h-4" />}
                </div>
                <div className="flex-1 space-y-0.5 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-warmgray-900">{log.action}</span>
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-bold font-mono bg-warmgray-100 text-warmgray-700">
                      {log.category}
                    </span>
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold font-mono ${
                      log.status === 'SUCCESS' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {log.status}
                    </span>
                  </div>
                  <p className="text-warmgray-600 font-medium truncate">
                    {log.description}
                  </p>
                </div>
                <span className="text-warmgray-400 font-mono text-[11px] shrink-0">
                  {log.created_at ? new Date(log.created_at).toLocaleTimeString() : 'Recently'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
