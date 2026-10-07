import React, { useState, useEffect } from 'react';
import {
  History as HistoryIcon,
  Search,
  Sprout,
  Eye,
  ShieldCheck,
  X,
  Clock
} from 'lucide-react';
import { getLeafDiseaseHistory, LeafDiseaseAnalysisResponse, NACLProductRecommendation } from '../api/leafDisease';

export const HistoryPage: React.FC = () => {
  const [scans, setScans] = useState<LeafDiseaseAnalysisResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedScan, setSelectedScan] = useState<LeafDiseaseAnalysisResponse | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await getLeafDiseaseHistory(50);
        setScans(data);
      } catch (err) {
        console.error('Failed to load scan history:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const filteredScans = React.useMemo(() => {
    return scans.filter((scan) => {
      const matchesStatus = filterStatus === 'ALL' || scan.status === filterStatus;
      const q = searchQuery.toLowerCase();
      const matchesQuery =
        !q ||
        scan.analysis_id.toLowerCase().includes(q) ||
        scan.crop?.crop_name?.toLowerCase().includes(q) ||
        scan.disease?.disease_name?.toLowerCase().includes(q);
      return matchesStatus && matchesQuery;
    });
  }, [scans, filterStatus, searchQuery]);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 shadow-xs flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3.5 rounded-2xl bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0]">
            <HistoryIcon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-warmgray-900 tracking-tight">
              Scan History & Audit Trail
            </h1>
            <p className="text-xs text-warmgray-500 font-medium mt-1">
              Historical record of leaf pathology analyses, Gemini VLM evidence calibration, and NACL recommendations.
            </p>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Status Tabs */}
        <div className="flex items-center gap-1.5 w-full sm:w-auto">
          {['ALL', 'SUCCESS', 'UNCERTAIN', 'FAILED'].map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setFilterStatus(st)}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                filterStatus === st
                  ? 'bg-[#d96b27] text-white shadow-xs'
                  : 'bg-white border border-[#e5ded3] text-warmgray-700 hover:bg-warmgray-50'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Search Bar */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-warmgray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by Crop, Disease, or ID..."
            className="w-full bg-white border border-[#e5ded3] rounded-xl pl-9 pr-4 py-2 text-xs font-medium text-warmgray-800 focus:outline-none focus:ring-2 focus:ring-[#d96b27]/30 focus:border-[#d96b27] transition-all"
          />
        </div>
      </div>

      {/* History List Container */}
      <div className="bg-white border border-[#eae4dc] rounded-2xl shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs font-bold font-mono text-warmgray-500 space-y-2">
            <Clock className="w-6 h-6 animate-spin text-[#d96b27] mx-auto" />
            <div>Fetching scan records from database...</div>
          </div>
        ) : filteredScans.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <div className="w-12 h-12 rounded-full bg-warmgray-100 text-warmgray-400 flex items-center justify-center mx-auto">
              <HistoryIcon className="w-6 h-6" />
            </div>
            <div className="text-sm font-bold text-warmgray-800">No matching scan history found</div>
            <p className="text-xs text-warmgray-500 font-mono">
              Try modifying your search filter or start a new scan.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-[#f1eee9]">
            {filteredScans.map((scan) => {
              const isSuccess = scan.status === 'SUCCESS';
              const isUncertain = scan.status === 'UNCERTAIN';
              const confidenceVal = scan.disease?.confidence;

              return (
                <div
                  key={scan.analysis_id}
                  onClick={() => setSelectedScan(scan)}
                  className="p-4 hover:bg-[#fdf3ed]/40 transition-colors flex items-center justify-between gap-4 cursor-pointer group"
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0] flex items-center justify-center shrink-0">
                      <Sprout className="w-5 h-5" />
                    </div>

                    <div className="min-w-0 space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-extrabold text-sm text-warmgray-900 group-hover:text-[#d96b27] transition-colors">
                          {scan.crop?.crop_name || 'Plant Foliage'}
                        </span>
                        <span className="text-xs text-warmgray-500 font-medium">
                          • {scan.disease?.disease_name || 'Condition Analysed'}
                        </span>
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold font-mono ${
                            isSuccess
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : isUncertain
                              ? 'bg-amber-50 text-amber-700 border border-amber-200'
                              : 'bg-red-50 text-red-700 border border-red-200'
                          }`}
                        >
                          {scan.status}
                        </span>
                      </div>

                      <div className="flex items-center gap-3 text-xs text-warmgray-500 font-mono flex-wrap">
                        <span>ID: {scan.analysis_id}</span>
                        <span>•</span>
                        <span>{new Date(scan.timestamp).toLocaleString()}</span>
                        {confidenceVal !== undefined && (
                          <>
                            <span>•</span>
                            <span className="text-[#d96b27] font-bold">
                              {(confidenceVal * 100).toFixed(0)}% Confidence
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="px-3.5 py-1.5 rounded-xl border border-[#e5ded3] bg-white text-xs font-bold text-warmgray-700 group-hover:border-[#d96b27] group-hover:text-[#d96b27] transition-colors flex items-center gap-1.5 shrink-0 shadow-xs"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View Details</span>
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedScan && (
        <div className="fixed inset-0 z-50 bg-warmgray-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-[#eae4dc] rounded-2xl max-w-2xl w-full p-6 space-y-6 shadow-2xl max-h-[90vh] overflow-y-auto animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-[#f1eee9] pb-4">
              <div>
                <span className="text-[10px] font-bold font-mono text-[#d96b27] uppercase tracking-wider">
                  Analysis Details
                </span>
                <h2 className="text-xl font-extrabold text-warmgray-900">
                  {selectedScan.crop?.crop_name} — {selectedScan.disease?.disease_name}
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setSelectedScan(null)}
                className="p-1.5 rounded-lg text-warmgray-400 hover:text-warmgray-700 hover:bg-warmgray-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content summary */}
            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-[#fdf3ed]/60 border border-[#f5d5c0]">
                <div>
                  <div className="text-[10px] font-bold text-warmgray-500 uppercase font-mono">Status</div>
                  <div className="font-extrabold text-warmgray-900">{selectedScan.status}</div>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-warmgray-500 uppercase font-mono">Timestamp</div>
                  <div className="font-extrabold text-warmgray-900">
                    {new Date(selectedScan.timestamp).toLocaleString()}
                  </div>
                </div>
              </div>

              {selectedScan.nacl_recommendations?.ai_advisory_summary && (
                <div className="space-y-1.5 p-4 rounded-xl bg-warmgray-50 border border-warmgray-200">
                  <div className="font-bold text-warmgray-900 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-[#d96b27]" />
                    <span>Agronomist Advisory Summary</span>
                  </div>
                  <p className="text-warmgray-700 leading-relaxed">
                    {selectedScan.nacl_recommendations.ai_advisory_summary}
                  </p>
                </div>
              )}

              {selectedScan.nacl_recommendations?.recommendations && selectedScan.nacl_recommendations.recommendations.length > 0 && (
                <div className="space-y-2">
                  <div className="font-bold text-warmgray-900">
                    Verified NACL Recommendations ({selectedScan.nacl_recommendations.recommendations.length})
                  </div>
                  <div className="space-y-2">
                    {selectedScan.nacl_recommendations.recommendations.map((rec: NACLProductRecommendation, i: number) => (
                      <div key={i} className="p-3 rounded-xl border border-[#eae4dc] bg-white flex items-center justify-between">
                        <div>
                          <div className="font-bold text-warmgray-900">{rec.product_name}</div>
                          <div className="text-[11px] text-warmgray-500">{rec.active_ingredient || 'Formulated Agrochemical'}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-mono font-bold text-[#d96b27]">{rec.recommended_dosage}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-[#f1eee9] flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedScan(null)}
                className="px-4 py-2 rounded-xl bg-[#d96b27] text-white text-xs font-bold hover:bg-[#c55d1d] transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
