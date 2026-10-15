import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  History as HistoryIcon,
  Search,
  Sprout,
  Eye,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  X,
  Clock,
  Stethoscope,
  Bug,
  FlaskConical,
  ArrowRight,
  Trash2,
  User,
  Lock,
  Layers,
  Sparkles,
  Info,
  Calendar,
  MapPin,
  CloudRain,
  Maximize2,
  ExternalLink,
  Check,
  Award
} from 'lucide-react';
import {
  getLeafDiseaseHistory,
  deleteLeafDiseaseRun,
  clearLeafDiseaseHistory,
  LeafDiseaseAnalysisResponse,
  NACLProductRecommendation
} from '../api/leafDisease';
import { getCurrentUserId } from '../api/client';

const PRESET_USER_MAP: Record<string, string> = {
  usr_agronomist_01: 'Abhinav Govardhana (Lead Agronomist)',
  usr_farmer_bob: 'Farmer Bob (Farm Owner)',
  usr_researcher_03: 'Dr. Alice Chen (Pathology Researcher)',
};

export const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeUserId, setActiveUserId] = useState<string>(getCurrentUserId());
  const [scans, setScans] = useState<LeafDiseaseAnalysisResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<'ALL' | 'DIAGNOSIS' | 'ADVISORY'>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedScan, setSelectedScan] = useState<LeafDiseaseAnalysisResponse | null>(null);
  const [activeModalTab, setActiveModalTab] = useState<'diagnosis' | 'advisory'>('diagnosis');
  const [enlargedImage, setEnlargedImage] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [brokenImages, setBrokenImages] = useState<Record<string, boolean>>({});

  // Resolves the best persistent specimen image for a scan, with fallback to advisory/parent scan
  const getResolvedSpecimenImage = React.useCallback(
    (scan: LeafDiseaseAnalysisResponse | null): string | null => {
      if (!scan) return null;
      if (brokenImages[scan.analysis_id]) return null;

      // 1. Direct scan image if valid and not an ephemeral blob:
      const directImg = scan.image_url;
      if (directImg && !directImg.startsWith('blob:') && !brokenImages[directImg]) {
        return directImg;
      }

      // 2. Advisory sub-document image if present
      const advImg = scan.advisory?.image_url;
      if (advImg && !advImg.startsWith('blob:') && !brokenImages[advImg]) {
        return advImg;
      }

      // 3. Parent analysis inspection image if linked
      if (scan.parent_analysis_id) {
        const parent = scans.find(
          (s) => s.analysis_id === scan.parent_analysis_id || (s as any)._id === scan.parent_analysis_id
        );
        if (parent?.image_url && !parent.image_url.startsWith('blob:') && !brokenImages[parent.image_url]) {
          return parent.image_url;
        }
      }

      return null;
    },
    [scans, brokenImages]
  );


  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await getLeafDiseaseHistory(50);
      setScans(data);
    } catch (err) {
      console.error('Failed to load scan history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();

    const handleUserChange = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail && detail.userId) {
        setActiveUserId(detail.userId);
        fetchHistory();
      }
    };
    window.addEventListener('kweka_user_changed', handleUserChange);
    return () => window.removeEventListener('kweka_user_changed', handleUserChange);
  }, []);

  const handleDeleteScan = async (analysisId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!window.confirm(`Are you sure you want to delete history record "${analysisId}"?`)) return;
    setDeletingId(analysisId);
    try {
      await deleteLeafDiseaseRun(analysisId);
      setScans((prev) => prev.filter((s) => s.analysis_id !== analysisId));
      if (selectedScan?.analysis_id === analysisId) {
        setSelectedScan(null);
      }
    } catch (err) {
      alert('Failed to delete history record.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAllHistory = async () => {
    if (
      !window.confirm(
        `Are you sure you want to clear all ${scans.length} historical records for user "${activeUserId}"? This action cannot be undone and will only purge records belonging to this user.`
      )
    ) {
      return;
    }
    setLoading(true);
    try {
      await clearLeafDiseaseHistory();
      setScans([]);
    } catch (err) {
      alert('Failed to clear user history.');
    } finally {
      setLoading(false);
    }
  };

  const currentDisplayName = PRESET_USER_MAP[activeUserId] || activeUserId;

  const filteredScans = React.useMemo(() => {
    return scans.filter((scan) => {
      // Type filter
      if (filterType === 'DIAGNOSIS' && scan.source === 'LEAF_ADVISORY') return false;
      if (filterType === 'ADVISORY' && scan.source !== 'LEAF_ADVISORY') return false;

      // Status filter
      const matchesStatus = filterStatus === 'ALL' || scan.status === filterStatus;

      // Search query
      const q = searchQuery.toLowerCase();
      const pestName = scan.pest?.primary_pest?.toLowerCase() || '';
      const cropName = scan.crop?.crop_name?.toLowerCase() || '';
      const diseaseName = scan.disease?.disease_name?.toLowerCase() || '';
      const advisorySummary = scan.ai_advisory_summary?.toLowerCase() || '';
      const geo = scan.geolocation?.toLowerCase() || '';
      const season = scan.season?.toLowerCase() || '';

      const matchesQuery =
        !q ||
        scan.analysis_id.toLowerCase().includes(q) ||
        cropName.includes(q) ||
        diseaseName.includes(q) ||
        pestName.includes(q) ||
        advisorySummary.includes(q) ||
        geo.includes(q) ||
        season.includes(q);

      return matchesStatus && matchesQuery;
    });
  }, [scans, filterType, filterStatus, searchQuery]);

  // Open modal with appropriate default tab
  const handleOpenDetails = (scan: LeafDiseaseAnalysisResponse) => {
    setSelectedScan(scan);
    if (scan.source === 'LEAF_ADVISORY') {
      setActiveModalTab('advisory');
    } else {
      setActiveModalTab('diagnosis');
    }
  };

  // Resolve best confidence string for row display
  const getDisplayConfidenceBadge = (scan: LeafDiseaseAnalysisResponse) => {
    if (scan.source === 'LEAF_ADVISORY') {
      const riskLevel = scan.seasonal_risk?.disease_pressure_level || scan.advisory?.seasonal_risk?.disease_pressure_level;
      if (riskLevel) {
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
            <CloudRain className="w-3 h-3 text-emerald-600" />
            Risk: {riskLevel}
          </span>
        );
      }
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold font-mono text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-200">
          <Stethoscope className="w-3 h-3 text-teal-600" />
          Agronomic Advisory
        </span>
      );
    }

    // Diagnosis Confidence Resolution
    const disConf = scan.disease?.confidence;
    const pestConf = scan.pest?.confidence;
    const cropConf = scan.crop?.confidence;

    if (disConf !== undefined && disConf !== null && disConf > 0) {
      return (
        <span className="text-[#d96b27] font-bold font-mono text-xs">
          {(disConf * 100).toFixed(0)}% Disease Conf.
        </span>
      );
    }
    if (pestConf !== undefined && pestConf !== null && pestConf > 0) {
      return (
        <span className="text-rose-600 font-bold font-mono text-xs">
          {(pestConf * 100).toFixed(0)}% Pest Conf.
        </span>
      );
    }
    if (cropConf !== undefined && cropConf !== null && cropConf > 0) {
      return (
        <span className="text-emerald-700 font-bold font-mono text-xs">
          {(cropConf * 100).toFixed(0)}% Crop Conf.
        </span>
      );
    }

    return (
      <span className="text-warmgray-500 font-medium font-mono text-xs">
        Validated Inspection
      </span>
    );
  };

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
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span className="text-xs text-warmgray-500 font-medium">
                Historical record for workspace:
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#fdeade] text-[#d96b27] text-xs font-bold font-mono border border-[#f5d5c0]">
                <User className="w-3 h-3 text-[#d96b27]" />
                {currentDisplayName}
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-mono font-bold border border-emerald-200">
                <Lock className="w-3 h-3 text-emerald-600" />
                User-Isolated
              </span>
            </div>
          </div>
        </div>

        {scans.length > 0 && (
          <button
            type="button"
            onClick={handleClearAllHistory}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-red-200 bg-red-50 text-red-700 text-xs font-bold hover:bg-red-100 transition-colors shadow-xs cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear My History</span>
          </button>
        )}
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Type & Status Filter Tabs */}
        <div className="flex items-center gap-2 flex-wrap w-full md:w-auto">
          {/* Category tabs */}
          <div className="flex items-center gap-1 p-1 bg-warmgray-100/80 rounded-xl border border-warmgray-200/80">
            <button
              type="button"
              onClick={() => setFilterType('ALL')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                filterType === 'ALL'
                  ? 'bg-white text-warmgray-900 shadow-xs'
                  : 'text-warmgray-600 hover:text-warmgray-900'
              }`}
            >
              All Records ({scans.length})
            </button>
            <button
              type="button"
              onClick={() => setFilterType('DIAGNOSIS')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                filterType === 'DIAGNOSIS'
                  ? 'bg-white text-[#d96b27] shadow-xs'
                  : 'text-warmgray-600 hover:text-warmgray-900'
              }`}
            >
              Diagnoses ({scans.filter((s) => s.source !== 'LEAF_ADVISORY').length})
            </button>
            <button
              type="button"
              onClick={() => setFilterType('ADVISORY')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                filterType === 'ADVISORY'
                  ? 'bg-white text-teal-700 shadow-xs'
                  : 'text-warmgray-600 hover:text-warmgray-900'
              }`}
            >
              Leaf Advisories ({scans.filter((s) => s.source === 'LEAF_ADVISORY').length})
            </button>
          </div>

          {/* Status selector */}
          <div className="flex items-center gap-1">
            {['ALL', 'SUCCESS', 'UNCERTAIN'].map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => setFilterStatus(st)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  filterStatus === st
                    ? 'bg-[#d96b27] text-white shadow-xs'
                    : 'bg-white border border-[#e5ded3] text-warmgray-700 hover:bg-warmgray-50'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-warmgray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search crop, disease, pest, region..."
            className="w-full bg-white border border-[#e5ded3] rounded-xl pl-9 pr-4 py-2 text-xs font-medium text-warmgray-800 focus:outline-none focus:ring-2 focus:ring-[#d96b27]/30 focus:border-[#d96b27] transition-all"
          />
        </div>
      </div>

      {/* History List Container */}
      <div className="bg-white border border-[#eae4dc] rounded-2xl shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs font-bold font-mono text-warmgray-500 space-y-2">
            <Clock className="w-6 h-6 animate-spin text-[#d96b27] mx-auto" />
            <div>Fetching scan & advisory records from database...</div>
          </div>
        ) : filteredScans.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <div className="w-12 h-12 rounded-full bg-warmgray-100 text-warmgray-400 flex items-center justify-center mx-auto">
              <HistoryIcon className="w-6 h-6" />
            </div>
            <div className="text-sm font-bold text-warmgray-800">No matching history records found</div>
            <p className="text-xs text-warmgray-500 font-mono">
              Try modifying your search filter or perform a new scan/advisory.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-[#f1eee9]">
            {filteredScans.map((scan) => {
              const isAdvisory = scan.source === 'LEAF_ADVISORY';
              const isSuccess = scan.status === 'SUCCESS';
              const isUncertain = scan.status === 'UNCERTAIN';
              const hasLinkedAdvisory = Boolean(scan.advisory || scan.has_advisory);

              return (
                <div
                  key={scan.analysis_id}
                  onClick={() => handleOpenDetails(scan)}
                  className="p-4 hover:bg-[#fdf3ed]/40 transition-colors flex items-center justify-between gap-4 cursor-pointer group"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    {/* Thumbnail Specimen or Icon */}
                    {(() => {
                      const rowSpecimen = getResolvedSpecimenImage(scan);
                      if (rowSpecimen) {
                        return (
                          <div
                            onClick={(e) => {
                              e.stopPropagation();
                              setEnlargedImage(rowSpecimen);
                            }}
                            className="relative w-12 h-12 rounded-xl overflow-hidden border border-[#eae4dc] shrink-0 bg-warmgray-100 cursor-pointer group/thumb"
                            title="Click to view high-res specimen"
                          >
                            <img
                              src={rowSpecimen}
                              alt="Specimen"
                              onError={() =>
                                setBrokenImages((prev) => ({
                                  ...prev,
                                  [scan.analysis_id]: true,
                                  [rowSpecimen]: true,
                                }))
                              }
                              className="w-full h-full object-cover group-hover/thumb:scale-105 transition-transform duration-200"
                            />
                          </div>
                        );
                      }

                      return (
                        <div
                          className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border ${
                            isAdvisory
                              ? 'bg-teal-50 text-teal-600 border-teal-200'
                              : 'bg-[#fdf3ed] text-[#d96b27] border-[#f5d5c0]'
                          }`}
                        >
                          {isAdvisory ? <Stethoscope className="w-6 h-6" /> : <Sprout className="w-6 h-6" />}
                        </div>
                      );
                    })()}


                    <div className="min-w-0 space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        {/* Source Tag */}
                        {isAdvisory ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-teal-50 text-teal-800 border border-teal-200 font-mono">
                            <Stethoscope className="w-3 h-3 text-teal-600" />
                            Leaf Advisory
                          </span>
                        ) : scan.source === 'LEAF_DIAGNOSIS' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 font-mono">
                            <FlaskConical className="w-3 h-3 text-indigo-600" />
                            Leaf Diagnosis
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0] font-mono">
                            <Sprout className="w-3 h-3 text-[#d96b27]" />
                            Leaf Scanner
                          </span>
                        )}

                        {/* Title: Crop */}
                        <span className="font-extrabold text-sm text-warmgray-900 group-hover:text-[#d96b27] transition-colors truncate">
                          {scan.crop?.crop_name || scan.advisory?.crop_name || 'Plant Foliage'}
                        </span>

                        {/* Disease finding */}
                        {scan.disease?.disease_name && !scan.disease.disease_name.toLowerCase().includes('no pathology') && (
                          <span className="text-xs text-warmgray-600 font-medium truncate">
                            • {scan.disease.disease_name}
                          </span>
                        )}

                        {/* Pest finding */}
                        {scan.pest?.primary_pest && !scan.pest.primary_pest.toLowerCase().includes('no pest') && (
                          <span className="text-xs text-rose-600 font-semibold flex items-center gap-1 truncate">
                            • <Bug className="w-3 h-3 text-rose-500 shrink-0" /> {scan.pest.primary_pest}
                          </span>
                        )}

                        {/* Advisory condition if standalone advisory */}
                        {isAdvisory && (scan.season || scan.geolocation) && (
                          <span className="text-xs text-teal-700 font-medium flex items-center gap-1">
                            • {scan.season || 'All Season'} ({scan.geolocation || 'General'})
                          </span>
                        )}

                        {/* Attached Advisory Pill */}
                        {hasLinkedAdvisory && !isAdvisory && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono">
                            <Check className="w-3 h-3 text-emerald-600" />
                            Advisory Done
                          </span>
                        )}

                        {/* Status Badge */}
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ${
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

                      {/* Sub-line metadata */}
                      <div className="flex items-center gap-2.5 text-xs text-warmgray-500 font-mono flex-wrap">
                        <span>ID: {scan.analysis_id.slice(0, 16)}...</span>
                        <span>•</span>
                        <span>{new Date(scan.timestamp).toLocaleString()}</span>
                        <span>•</span>
                        {getDisplayConfidenceBadge(scan)}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {!isAdvisory && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate('/leaf-advisory', {
                            state: {
                              inspection_id: scan.analysis_id,
                              diagnosis: {
                                analysis_id: scan.analysis_id,
                                crop_name: scan.crop?.crop_name,
                                disease_name: scan.disease?.disease_name,
                                pest_name: scan.pest?.primary_pest,
                                confidence: scan.disease?.confidence || scan.crop?.confidence || 0.85,
                                source: scan.source || 'LEAF_DIAGNOSIS',
                                timestamp: scan.timestamp,
                                image_url: scan.image_url || null,
                                summary: `Crop: ${scan.crop?.crop_name}${scan.disease?.disease_name ? ` • Disease: ${scan.disease.disease_name}` : ''}${scan.pest?.primary_pest ? ` • Pest: ${scan.pest.primary_pest}` : ''}`
                              },
                              imageUrl: scan.image_url || null
                            }
                          });
                        }}
                        className="px-3 py-1.5 rounded-xl border border-[#f5d5c0] bg-[#fdf3ed] text-xs font-bold text-[#d96b27] hover:bg-[#fdeade] transition-colors flex items-center gap-1.5 shadow-xs cursor-pointer"
                        title="Generate Leaf Advisory remedies for this record"
                      >
                        <Stethoscope className="w-3.5 h-3.5 text-[#d96b27]" />
                        <span className="hidden sm:inline">Advisory</span>
                        <ArrowRight className="w-3 h-3 text-[#d96b27]" />
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenDetails(scan);
                      }}
                      className="px-3.5 py-1.5 rounded-xl border border-[#e5ded3] bg-white text-xs font-bold text-warmgray-700 group-hover:border-[#d96b27] group-hover:text-[#d96b27] transition-colors flex items-center gap-1.5 shadow-xs cursor-pointer"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Details</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Comprehensive Report Details Modal */}
      {selectedScan && (
        <div className="fixed inset-0 z-50 bg-warmgray-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-6 overflow-y-auto">
          <div className="bg-white border border-[#eae4dc] rounded-2xl max-w-4xl w-full p-6 space-y-6 shadow-2xl max-h-[92vh] overflow-y-auto animate-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-[#f1eee9] pb-4 gap-4">
              <div className="flex items-center gap-3.5 min-w-0">
                {(() => {
                  const modalSpecimen = getResolvedSpecimenImage(selectedScan);
                  const isAdv = selectedScan.source === 'LEAF_ADVISORY';

                  if (modalSpecimen) {
                    return (
                      <div
                        onClick={() => setEnlargedImage(modalSpecimen)}
                        className="relative w-16 h-16 sm:w-20 sm:h-20 rounded-2xl overflow-hidden border border-[#eae4dc] bg-warmgray-100 shrink-0 cursor-pointer group/img shadow-xs"
                        title="Click to enlarge specimen"
                      >
                        <img
                          src={modalSpecimen}
                          alt="Analyzed Specimen"
                          onError={() =>
                            setBrokenImages((prev) => ({
                              ...prev,
                              [selectedScan.analysis_id]: true,
                              [modalSpecimen]: true,
                            }))
                          }
                          className="w-full h-full object-cover group-hover/img:scale-110 transition-transform duration-200"
                        />
                        <div className="absolute inset-0 bg-black/35 opacity-0 group-hover/img:opacity-100 flex items-center justify-center transition-opacity">
                          <Maximize2 className="w-5 h-5 text-white" />
                        </div>
                      </div>
                    );
                  }

                  return (
                    <div
                      className={`w-16 h-16 sm:w-20 sm:h-20 rounded-2xl border flex flex-col items-center justify-center shrink-0 shadow-xs ${
                        isAdv
                          ? 'bg-teal-50 text-teal-600 border-teal-200'
                          : 'bg-[#fdf3ed] text-[#d96b27] border-[#f5d5c0]'
                      }`}
                      title="Specimen telemetry record"
                    >
                      {isAdv ? (
                        <Stethoscope className="w-7 h-7 sm:w-8 sm:h-8" />
                      ) : (
                        <Sprout className="w-7 h-7 sm:w-8 sm:h-8" />
                      )}
                    </div>
                  );
                })()}

                <div className="min-w-0 space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] font-bold font-mono text-[#d96b27] uppercase tracking-wider bg-[#fdf3ed] px-2 py-0.5 rounded border border-[#f5d5c0]">
                      {selectedScan.source === 'LEAF_ADVISORY'
                        ? 'Leaf Advisory Report'
                        : selectedScan.source === 'LEAF_DIAGNOSIS'
                        ? 'Unified Leaf Diagnosis'
                        : 'Leaf Inspection'}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                        selectedScan.status === 'SUCCESS'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}
                    >
                      {selectedScan.status}
                    </span>
                  </div>
                  <h2 className="text-xl font-extrabold text-warmgray-900 leading-tight">
                    {selectedScan.crop?.crop_name || selectedScan.advisory?.crop_name}
                    {selectedScan.disease?.disease_name && ` — ${selectedScan.disease.disease_name}`}
                    {selectedScan.pest?.primary_pest &&
                      !selectedScan.pest.primary_pest.toLowerCase().includes('no pest') &&
                      ` (Pest: ${selectedScan.pest.primary_pest})`}
                  </h2>
                  <div className="flex items-center gap-3 text-xs text-warmgray-500 font-mono flex-wrap">
                    <span>ID: {selectedScan.analysis_id}</span>
                    <span>•</span>
                    <span>{new Date(selectedScan.timestamp).toLocaleString()}</span>
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setSelectedScan(null)}
                className="p-2 rounded-xl text-warmgray-400 hover:text-warmgray-700 hover:bg-warmgray-100 transition-colors shrink-0 cursor-pointer"
                title="Close Modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Tabs if scan has both Diagnosis and Leaf Advisory */}
            {(selectedScan.advisory || selectedScan.has_advisory || selectedScan.source === 'LEAF_ADVISORY') &&
              selectedScan.source !== 'LEAF_ADVISORY' && (
                <div className="flex items-center gap-2 border-b border-[#f1eee9] pb-3">
                  <button
                    type="button"
                    onClick={() => setActiveModalTab('diagnosis')}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                      activeModalTab === 'diagnosis'
                        ? 'bg-[#d96b27] text-white shadow-xs'
                        : 'bg-warmgray-50 text-warmgray-700 hover:bg-warmgray-100'
                    }`}
                  >
                    <FlaskConical className="w-3.5 h-3.5" />
                    <span>Complete Diagnosis Report</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveModalTab('advisory')}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                      activeModalTab === 'advisory'
                        ? 'bg-teal-700 text-white shadow-xs'
                        : 'bg-teal-50 text-teal-800 border border-teal-200 hover:bg-teal-100'
                    }`}
                  >
                    <Stethoscope className="w-3.5 h-3.5" />
                    <span>Agronomic Advisory Report</span>
                    <span className="px-1.5 py-0.2 rounded text-[9px] bg-white/20 font-mono font-bold">
                      Generated
                    </span>
                  </button>
                </div>
              )}

            {/* TAB 1: DIAGNOSIS REPORT */}
            {activeModalTab === 'diagnosis' && selectedScan.source !== 'LEAF_ADVISORY' && (
              <div className="space-y-5 text-xs animate-in fade-in duration-150">
                {/* 1. Botanical Crop & Pathology Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Crop Specimen Card */}
                  <div className="p-4 rounded-xl bg-warmgray-50 border border-warmgray-200 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <div className="font-bold text-warmgray-900 flex items-center gap-1.5">
                        <Sprout className="w-4 h-4 text-[#d96b27]" />
                        <span>Botanical Crop Identification</span>
                      </div>
                      {selectedScan.crop?.status && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-100 text-emerald-800">
                          {selectedScan.crop.status}
                        </span>
                      )}
                    </div>

                    <div className="space-y-1">
                      <div className="text-base font-extrabold text-warmgray-900">
                        {selectedScan.crop?.crop_name || 'Unspecified'}
                      </div>
                      {selectedScan.crop?.scientific_name && (
                        <div className="text-xs italic text-warmgray-500 font-mono">
                          {selectedScan.crop.scientific_name}
                        </div>
                      )}
                      {selectedScan.crop?.confidence !== undefined && selectedScan.crop?.confidence !== null && (
                        <div className="pt-1 flex items-center gap-2">
                          <div className="flex-1 bg-warmgray-200 h-1.5 rounded-full overflow-hidden">
                            <div
                              className="bg-[#d96b27] h-full rounded-full"
                              style={{ width: `${Math.min(100, selectedScan.crop.confidence * 100)}%` }}
                            />
                          </div>
                          <span className="font-mono font-bold text-[#d96b27]">
                            {(selectedScan.crop.confidence * 100).toFixed(0)}% Confidence
                          </span>
                        </div>
                      )}
                    </div>

                    {selectedScan.crop?.message && (
                      <p className="text-[11px] text-warmgray-600 bg-white p-2.5 rounded-lg border border-warmgray-200/80 leading-relaxed">
                        {selectedScan.crop.message}
                      </p>
                    )}
                  </div>

                  {/* Disease Pathology Card */}
                  <div className="p-4 rounded-xl bg-warmgray-50 border border-warmgray-200 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <div className="font-bold text-warmgray-900 flex items-center gap-1.5">
                        <ShieldAlert className="w-4 h-4 text-[#d96b27]" />
                        <span>Foliar Disease Pathology</span>
                      </div>
                      {selectedScan.disease?.status && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-indigo-100 text-indigo-800">
                          {selectedScan.disease.status}
                        </span>
                      )}
                    </div>

                    <div className="space-y-1">
                      <div className="text-base font-extrabold text-warmgray-900">
                        {selectedScan.disease?.disease_name || 'No pathology detected'}
                      </div>
                      {selectedScan.disease?.scientific_name && (
                        <div className="text-xs italic text-warmgray-500 font-mono">
                          {selectedScan.disease.scientific_name}
                        </div>
                      )}
                      {selectedScan.disease?.confidence !== undefined && selectedScan.disease?.confidence !== null && (
                        <div className="pt-1 flex items-center gap-2">
                          <div className="flex-1 bg-warmgray-200 h-1.5 rounded-full overflow-hidden">
                            <div
                              className="bg-indigo-600 h-full rounded-full"
                              style={{ width: `${Math.min(100, selectedScan.disease.confidence * 100)}%` }}
                            />
                          </div>
                          <span className="font-mono font-bold text-indigo-700">
                            {(selectedScan.disease.confidence * 100).toFixed(0)}% Confidence
                          </span>
                        </div>
                      )}
                    </div>

                    {selectedScan.disease?.message && (
                      <p className="text-[11px] text-warmgray-600 bg-white p-2.5 rounded-lg border border-warmgray-200/80 leading-relaxed">
                        {selectedScan.disease.message}
                      </p>
                    )}
                  </div>
                </div>

                {/* 2. Insect & Pest Identification */}
                {selectedScan.pest?.primary_pest &&
                  !selectedScan.pest.primary_pest.toLowerCase().includes('no pest') && (
                    <div className="p-4 rounded-xl bg-rose-50/70 border border-rose-200 space-y-2.5">
                      <div className="flex items-center justify-between">
                        <div className="font-bold text-rose-900 flex items-center gap-1.5">
                          <Bug className="w-4 h-4 text-rose-600" />
                          <span>Insect & Pest Diagnostics</span>
                        </div>
                        {selectedScan.pest.status && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-rose-200 text-rose-800">
                            {selectedScan.pest.status}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center justify-between gap-4 flex-wrap">
                        <div>
                          <div className="text-base font-extrabold text-slate-900">
                            {selectedScan.pest.primary_pest}
                          </div>
                          {selectedScan.pest.detected_pests?.[0]?.scientific_name && (
                            <div className="text-xs italic text-rose-700 font-mono">
                              {selectedScan.pest.detected_pests[0].scientific_name}
                            </div>
                          )}
                        </div>
                        {selectedScan.pest.confidence && (
                          <span className="font-mono text-rose-700 font-bold bg-white px-2.5 py-1 rounded-lg border border-rose-200">
                            {(selectedScan.pest.confidence * 100).toFixed(0)}% Morphological Confidence
                          </span>
                        )}
                      </div>

                      {selectedScan.pest.message && (
                        <p className="text-[11px] text-rose-800 bg-white p-2.5 rounded-lg border border-rose-200/80 leading-relaxed">
                          {selectedScan.pest.message}
                        </p>
                      )}
                    </div>
                  )}

                {/* 3. Cross-Validation & Reliability Engine Details */}
                {selectedScan.cross_validation && (
                  <div className="p-4 rounded-xl bg-slate-900 text-slate-100 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-emerald-400" />
                        <span className="font-extrabold text-sm text-white">
                          Reliability Engine & Multi-Model Consensus
                        </span>
                      </div>
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-700">
                        {selectedScan.cross_validation.reliability_tier || 'AUTHORITATIVE'} TIER
                      </span>
                    </div>

                    {selectedScan.cross_validation.diagnostic_verdict && (
                      <p className="text-xs text-slate-200 leading-relaxed bg-slate-800/80 p-3 rounded-lg border border-slate-700">
                        {selectedScan.cross_validation.diagnostic_verdict}
                      </p>
                    )}

                    {selectedScan.cross_validation.detected_contradictions &&
                      selectedScan.cross_validation.detected_contradictions.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[10px] font-bold text-amber-400 uppercase font-mono">
                            Diagnostic Contradiction Warnings:
                          </span>
                          {selectedScan.cross_validation.detected_contradictions.map((c: string, idx: number) => (
                            <div key={idx} className="text-[11px] text-amber-200 flex items-start gap-1.5">
                              <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                              <span>{c}</span>
                            </div>
                          ))}
                        </div>
                      )}
                  </div>
                )}

                {/* 4. Verified NACL Remedies (from Diagnosis) */}
                {selectedScan.nacl_recommendations?.recommendations &&
                  selectedScan.nacl_recommendations.recommendations.length > 0 && (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="font-bold text-warmgray-900 text-sm flex items-center gap-1.5">
                          <Award className="w-4 h-4 text-[#d96b27]" />
                          <span>
                            Verified NACL Product Recommendations (
                            {selectedScan.nacl_recommendations.recommendations.length})
                          </span>
                        </div>
                      </div>

                      {selectedScan.nacl_recommendations.ai_advisory_summary && (
                        <p className="p-3 bg-[#fdf3ed] rounded-xl border border-[#f5d5c0] text-warmgray-800 leading-relaxed">
                          {selectedScan.nacl_recommendations.ai_advisory_summary}
                        </p>
                      )}

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {selectedScan.nacl_recommendations.recommendations.map(
                          (rec: NACLProductRecommendation, i: number) => {
                            const isRank1 = rec.efficacy_rank === 1 || i === 0;
                            return (
                              <div
                                key={i}
                                className={`p-3.5 rounded-xl border flex flex-col justify-between space-y-2 ${
                                  isRank1
                                    ? 'bg-[#fdf3ed]/60 border-[#f5d5c0]'
                                    : 'bg-white border-[#eae4dc]'
                                }`}
                              >
                                <div className="space-y-1">
                                  <div className="flex items-center justify-between gap-2">
                                    <span
                                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                                        isRank1
                                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                          : 'bg-blue-100 text-blue-800 border border-blue-200'
                                      }`}
                                    >
                                      {rec.benefit_badge || `Rank #${rec.efficacy_rank || i + 1}`}
                                    </span>
                                    <span className="font-mono font-extrabold text-[#d96b27]">
                                      {rec.recommended_dosage}
                                    </span>
                                  </div>
                                  <div className="font-extrabold text-sm text-warmgray-900">
                                    {rec.product_name}
                                  </div>
                                  <div className="text-[11px] text-warmgray-600 font-medium">
                                    {rec.active_ingredient || 'Formulated Agrochemical'}
                                  </div>
                                </div>

                                {rec.benefit_reason && (
                                  <p className="text-[11px] text-warmgray-600 italic border-t border-warmgray-200/60 pt-1.5">
                                    {rec.benefit_reason}
                                  </p>
                                )}
                              </div>
                            );
                          }
                        )}
                      </div>
                    </div>
                  )}
              </div>
            )}

            {/* TAB 2: COMPLETE LEAF ADVISORY REPORT */}
            {(activeModalTab === 'advisory' || selectedScan.source === 'LEAF_ADVISORY') && (
              <div className="space-y-5 text-xs animate-in fade-in duration-150">
                {/* Advisory Scope & Climate Card */}
                {(() => {
                  const adv = selectedScan.advisory || selectedScan;
                  const seasonalRisk = adv.seasonal_risk || selectedScan.seasonal_risk;
                  const naclProducts: NACLProductRecommendation[] =
                    adv.nacl_products || selectedScan.nacl_products || [];
                  const culturalRemedies: string[] =
                    adv.cultural_remedies || selectedScan.cultural_remedies || [];
                  const chemicalManagement: string[] =
                    adv.chemical_management || selectedScan.chemical_management || [];
                  const summaryText =
                    adv.ai_advisory_summary || selectedScan.ai_advisory_summary;

                  return (
                    <div className="space-y-5">
                      {/* Context Banner */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 rounded-xl bg-teal-50/70 border border-teal-200">
                        <div>
                          <div className="text-[10px] font-bold text-teal-700 uppercase font-mono flex items-center gap-1">
                            <Sprout className="w-3 h-3" /> Target Crop
                          </div>
                          <div className="font-extrabold text-teal-950 truncate">
                            {adv.crop_name || selectedScan.crop?.crop_name}
                          </div>
                        </div>

                        <div>
                          <div className="text-[10px] font-bold text-teal-700 uppercase font-mono flex items-center gap-1">
                            <Bug className="w-3 h-3" /> Diagnosed Condition
                          </div>
                          <div className="font-extrabold text-teal-950 truncate">
                            {adv.disease_name || adv.pest_name || 'General Health'}
                          </div>
                        </div>

                        <div>
                          <div className="text-[10px] font-bold text-teal-700 uppercase font-mono flex items-center gap-1">
                            <MapPin className="w-3 h-3" /> Region
                          </div>
                          <div className="font-extrabold text-teal-950 truncate">
                            {adv.geolocation || 'General Agricultural Region'}
                          </div>
                        </div>

                        <div>
                          <div className="text-[10px] font-bold text-teal-700 uppercase font-mono flex items-center gap-1">
                            <Calendar className="w-3 h-3" /> Season
                          </div>
                          <div className="font-extrabold text-teal-950 truncate">
                            {adv.season || 'General / All Season'}
                          </div>
                        </div>
                      </div>

                      {/* Seasonal Risk Assessment Card */}
                      {seasonalRisk && (
                        <div className="p-4 rounded-xl bg-warmgray-50 border border-warmgray-200 space-y-2.5">
                          <div className="flex items-center justify-between">
                            <div className="font-bold text-warmgray-900 flex items-center gap-1.5 text-sm">
                              <CloudRain className="w-4 h-4 text-teal-600" />
                              <span>Seasonal Climate & Disease Pressure Analysis</span>
                            </div>
                            <span
                              className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                                seasonalRisk.disease_pressure_level === 'HIGH'
                                  ? 'bg-rose-100 text-rose-800 border border-rose-300'
                                  : seasonalRisk.disease_pressure_level === 'MODERATE'
                                  ? 'bg-amber-100 text-amber-800 border border-amber-300'
                                  : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                              }`}
                            >
                              {seasonalRisk.disease_pressure_level} PRESSURE
                            </span>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                            <div className="p-3 bg-white rounded-lg border border-warmgray-200 space-y-1">
                              <div className="text-[10px] font-bold text-warmgray-500 uppercase font-mono">
                                Climate Factors
                              </div>
                              <p className="text-warmgray-700 leading-relaxed">
                                {seasonalRisk.climate_factors}
                              </p>
                            </div>
                            <div className="p-3 bg-white rounded-lg border border-warmgray-200 space-y-1">
                              <div className="text-[10px] font-bold text-warmgray-500 uppercase font-mono">
                                Weather Spray Window Advice
                              </div>
                              <p className="text-warmgray-700 leading-relaxed">
                                {seasonalRisk.weather_spray_window_advice}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Agronomist Advisory Synthesis */}
                      {summaryText && (
                        <div className="p-4 rounded-xl bg-[#fdf3ed]/70 border border-[#f5d5c0] space-y-2">
                          <div className="font-bold text-warmgray-900 flex items-center gap-1.5 text-sm">
                            <Sparkles className="w-4 h-4 text-[#d96b27]" />
                            <span>Expert Agronomist Synthesis</span>
                          </div>
                          <p className="text-warmgray-800 leading-relaxed whitespace-pre-line">
                            {summaryText}
                          </p>
                        </div>
                      )}

                      {/* Ranked Chemical Management Products */}
                      {naclProducts.length > 0 && (
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <div className="font-bold text-warmgray-900 text-sm flex items-center gap-1.5">
                              <Award className="w-4 h-4 text-[#d96b27]" />
                              <span>
                                Beneficial NACL Product Chemical Management ({naclProducts.length} verified)
                              </span>
                            </div>
                          </div>

                          <div className="space-y-2.5">
                            {naclProducts.map((prod: NACLProductRecommendation, idx: number) => {
                              const isRank1 = prod.efficacy_rank === 1 || idx === 0;
                              const isRank2 = prod.efficacy_rank === 2 || idx === 1;

                              return (
                                <div
                                  key={idx}
                                  className={`p-4 rounded-xl border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 ${
                                    isRank1
                                      ? 'bg-emerald-50/50 border-emerald-200'
                                      : isRank2
                                      ? 'bg-blue-50/50 border-blue-200'
                                      : 'bg-white border-[#eae4dc]'
                                  }`}
                                >
                                  <div className="space-y-1.5 min-w-0">
                                    <div className="flex items-center gap-2 flex-wrap">
                                      <span
                                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                                          isRank1
                                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                            : isRank2
                                            ? 'bg-blue-100 text-blue-800 border border-blue-300'
                                            : 'bg-amber-100 text-amber-800 border border-amber-300'
                                        }`}
                                      >
                                        {prod.benefit_badge || `Rank #${prod.efficacy_rank || idx + 1}`}
                                      </span>
                                      <span className="text-[10px] font-bold font-mono text-warmgray-500 uppercase">
                                        {prod.category}
                                      </span>
                                    </div>
                                    <div className="text-base font-extrabold text-warmgray-900">
                                      {prod.product_name}
                                    </div>
                                    <div className="text-xs text-warmgray-700 font-semibold flex items-center gap-1.5">
                                      <FlaskConical className="w-3.5 h-3.5 text-[#d96b27]" />
                                      <span>{prod.active_ingredient || 'Proprietary Formulation'}</span>
                                    </div>
                                    {prod.benefit_reason && (
                                      <p className="text-[11px] text-warmgray-600 italic">
                                        {prod.benefit_reason}
                                      </p>
                                    )}
                                  </div>

                                  <div className="md:text-right shrink-0">
                                    <div className="text-[10px] font-bold text-warmgray-500 uppercase font-mono">
                                      Prescribed Dosage
                                    </div>
                                    <div className="text-sm font-extrabold font-mono text-[#d96b27]">
                                      {prod.recommended_dosage}
                                    </div>
                                    {prod.application_guidelines && (
                                      <div className="text-[11px] text-warmgray-500 max-w-xs line-clamp-2 mt-0.5">
                                        {prod.application_guidelines}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Cultural & Preventative Practices */}
                      {culturalRemedies.length > 0 && (
                        <div className="p-4 rounded-xl bg-warmgray-50 border border-warmgray-200 space-y-2">
                          <div className="font-bold text-warmgray-900 flex items-center gap-1.5 text-sm">
                            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                            <span>Cultural & Preventative Agronomic Practices</span>
                          </div>
                          <ul className="space-y-1.5 pt-1">
                            {culturalRemedies.map((remedy: string, idx: number) => (
                              <li key={idx} className="flex items-start gap-2 text-warmgray-700">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 mt-1.5 shrink-0" />
                                <span className="leading-relaxed">{remedy}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Safety Precautions */}
                      {chemicalManagement.length > 0 && (
                        <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-200 space-y-2">
                          <div className="font-bold text-amber-900 flex items-center gap-1.5 text-sm">
                            <AlertTriangle className="w-4 h-4 text-amber-600" />
                            <span>Chemical Stewardship & Application Protocols</span>
                          </div>
                          <ul className="space-y-1.5 pt-1">
                            {chemicalManagement.map((step: string, idx: number) => (
                              <li key={idx} className="flex items-start gap-2 text-amber-900">
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-600 mt-1.5 shrink-0" />
                                <span className="leading-relaxed">{step}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>
            )}

            {/* Modal Footer Controls */}
            <div className="pt-4 border-t border-[#f1eee9] flex items-center justify-between gap-3 flex-wrap">
              {selectedScan.source !== 'LEAF_ADVISORY' && (
                <button
                  type="button"
                  onClick={() => {
                    const s = selectedScan;
                    const resolvedImg = getResolvedSpecimenImage(s);
                    setSelectedScan(null);
                    navigate('/leaf-advisory', {
                      state: {
                        inspection_id: s.analysis_id,
                        diagnosis: {
                          analysis_id: s.analysis_id,
                          crop_name: s.crop?.crop_name,
                          disease_name: s.disease?.disease_name,
                          pest_name: s.pest?.primary_pest,
                          confidence: s.disease?.confidence || s.crop?.confidence || 0.85,
                          source: s.source || 'LEAF_DIAGNOSIS',
                          timestamp: s.timestamp,
                          image_url: resolvedImg || null,
                          summary: `Crop: ${s.crop?.crop_name}${s.disease?.disease_name ? ` • Disease: ${s.disease.disease_name}` : ''}${s.pest?.primary_pest ? ` • Pest: ${s.pest.primary_pest}` : ''}`
                        },
                        imageUrl: resolvedImg || null
                      }
                    });

                  }}
                  className="px-4 py-2 rounded-xl bg-[#d96b27] hover:bg-[#c55d1d] active:scale-[0.98] text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm cursor-pointer"
                >
                  <Stethoscope className="w-3.5 h-3.5" />
                  <span>Launch New Leaf Advisory</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}

              <div className="flex items-center gap-2 ml-auto">
                <button
                  type="button"
                  onClick={() => handleDeleteScan(selectedScan.analysis_id)}
                  disabled={deletingId === selectedScan.analysis_id}
                  className="px-3.5 py-2 rounded-xl border border-red-200 bg-red-50 hover:bg-red-100 text-red-700 text-xs font-bold transition-colors flex items-center gap-1.5 cursor-pointer"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>{deletingId === selectedScan.analysis_id ? 'Deleting...' : 'Delete Record'}</span>
                </button>

                <button
                  type="button"
                  onClick={() => setSelectedScan(null)}
                  className="px-4 py-2 rounded-xl bg-warmgray-100 hover:bg-warmgray-200 text-warmgray-700 text-xs font-bold transition-colors cursor-pointer"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Enlarged Specimen Modal */}
      {enlargedImage && (
        <div
          onClick={() => setEnlargedImage(null)}
          className="fixed inset-0 z-60 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 cursor-zoom-out"
        >
          <div className="relative max-w-3xl max-h-[90vh] bg-black rounded-2xl overflow-hidden shadow-2xl">
            <img src={enlargedImage} alt="Specimen High-Res" className="w-full h-full object-contain" />
            <button
              type="button"
              onClick={() => setEnlargedImage(null)}
              className="absolute top-3 right-3 p-2 rounded-full bg-black/60 text-white hover:bg-black/90 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
