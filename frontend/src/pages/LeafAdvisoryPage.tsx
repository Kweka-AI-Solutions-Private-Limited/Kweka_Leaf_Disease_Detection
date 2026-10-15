import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Stethoscope,
  MapPin,
  Calendar,
  Sprout,
  ShieldAlert,
  Bug,
  ArrowRight,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Layers,
  Sparkles,
  Clock,
  PlusCircle,
  Search,
  ChevronRight,
  Check,
  RefreshCw,
  Sliders,
  HelpCircle,
  Printer,
  Maximize2,
  Thermometer,
  Wind,
  Droplets,
  Sun,
  ShieldCheck,
  Activity,
  FileText,
  Table as TableIcon,
  LayoutGrid,
  Eye,
  X,
  Scale,
  FlaskConical,
  Compass,
  ChevronDown,
  ChevronUp,
  Locate,
  BadgeAlert,
  Beaker,
  CheckSquare,
  Square
} from 'lucide-react';
import {
  getAdvisoryHistory,
  getAdvisoryOptions,
  generateLeafAdvisory,
  AdvisoryHistoricalDiagnosisItem,
  LeafAdvisoryResponse,
  AdvisoryOptionsResponse
} from '../api/leafAdvisory';

export const LeafAdvisoryPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Step state: 1 = choose diagnosis, 2 = select geolocation/season, 3 = view advisory
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);

  // Historical diagnoses state
  const [historyItems, setHistoryItems] = useState<AdvisoryHistoricalDiagnosisItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(true);
  const [searchHistory, setSearchHistory] = useState<string>('');

  // Selected Diagnosis & Specimen Image
  const [selectedDiagnosis, setSelectedDiagnosis] = useState<AdvisoryHistoricalDiagnosisItem | null>(null);
  const [specimenImageUrl, setSpecimenImageUrl] = useState<string | null>(null);

  // Optional Context: Geolocation & Season
  const [geolocation, setGeolocation] = useState<string>('');
  const [season, setSeason] = useState<string>('');
  const [optionsData, setOptionsData] = useState<AdvisoryOptionsResponse | null>(null);

  // Mandatory Quick Diagnosis Intake
  const [growthStage, setGrowthStage] = useState<string>('Vegetative');
  const [onsetDays, setOnsetDays] = useState<string>('1-2 days ago (Acute)');
  const [recentWeather, setRecentWeather] = useState<string>('Clear & Dry');
  const [previousTreatment, setPreviousTreatment] = useState<string>('None (First Spray)');

  // Optional Extended Agronomy Parameters
  const [areaSown, setAreaSown] = useState<string>('1.0');
  const [areaUnit, setAreaUnit] = useState<'acres' | 'hectares'>('acres');
  const [sowingDate, setSowingDate] = useState<string>('');
  const [cropVariety, setCropVariety] = useState<string>('');
  const [plantPartsAffected, setPlantPartsAffected] = useState<string[]>(['Leaf']);
  const [irrigationCondition, setIrrigationCondition] = useState<string>('Normal');
  const [severityLevel, setSeverityLevel] = useState<string>('Moderate (10-30%)');
  const [farmerName, setFarmerName] = useState<string>('');
  const [farmerPhone, setFarmerPhone] = useState<string>('');
  const [farmerNotes, setFarmerNotes] = useState<string>('');
  const [gpsCoordinates, setGpsCoordinates] = useState<string>('');
  const [isDetectingGps, setIsDetectingGps] = useState<boolean>(false);
  const [showExtendedFields, setShowExtendedFields] = useState<boolean>(false);

  // Advisory Results & Loading
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [advisoryResult, setAdvisoryResult] = useState<LeafAdvisoryResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Step 3 Interactive View States
  const [productViewMode, setProductViewMode] = useState<'table' | 'cards'>('table');
  const [productCategoryFilter, setProductCategoryFilter] = useState<string>('ALL');
  const [isImageModalOpen, setIsImageModalOpen] = useState<boolean>(false);
  const [specimenImageError, setSpecimenImageError] = useState<boolean>(false);
  const [failedHistoryImages, setFailedHistoryImages] = useState<Record<string, boolean>>({});


  useEffect(() => {
    fetchHistory();
    fetchOptions();

    const handleUserChange = () => {
      fetchHistory();
    };
    window.addEventListener('kweka_user_changed', handleUserChange);
    return () => window.removeEventListener('kweka_user_changed', handleUserChange);
  }, []);

  useEffect(() => {
    if (location.state?.diagnosis) {
      setSelectedDiagnosis(location.state.diagnosis);
      const img = location.state.imageUrl || location.state.diagnosis.image_url || null;
      if (img && !img.startsWith('blob:')) {
        setSpecimenImageUrl(img);
      } else {
        setSpecimenImageUrl(null);
      }
      setSpecimenImageError(false);
      setCurrentStep(2);
      setErrorMessage(null);
    }
  }, [location.state]);

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const data = await getAdvisoryHistory(50);
      setHistoryItems(data);
    } catch (err: any) {
      console.error('Failed to load diagnosis history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const fetchOptions = async () => {
    try {
      const data = await getAdvisoryOptions();
      setOptionsData(data);
    } catch (err: any) {
      console.error('Failed to load advisory options:', err);
    }
  };

  const handleSelectExistingDiagnosis = (item: AdvisoryHistoricalDiagnosisItem) => {
    setSelectedDiagnosis(item);
    if (item.image_url && !item.image_url.startsWith('blob:')) {
      setSpecimenImageUrl(item.image_url);
    } else {
      setSpecimenImageUrl(null);
    }
    setSpecimenImageError(false);
    setCurrentStep(2);
    setErrorMessage(null);
  };

  const handleDetectGps = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }
    setIsDetectingGps(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude.toFixed(4);
        const lon = position.coords.longitude.toFixed(4);
        const coordsStr = `${lat}, ${lon}`;
        setGpsCoordinates(coordsStr);
        if (!geolocation.trim()) {
          setGeolocation(`GPS Location (${coordsStr})`);
        }
        setIsDetectingGps(false);
      },
      (err) => {
        console.warn('Geolocation lookup failed:', err);
        setIsDetectingGps(false);
      },
      { timeout: 10000 }
    );
  };

  const handleGenerateAdvisory = async (skipOptional = false) => {
    if (!selectedDiagnosis) return;

    setIsGenerating(true);
    setErrorMessage(null);

    const geoVal = skipOptional ? null : (geolocation.trim() || null);
    const seasonVal = skipOptional ? null : (season.trim() || null);
    const candidateImg = specimenImageUrl || selectedDiagnosis.image_url || null;
    const resolvedSpecimen = candidateImg && !candidateImg.startsWith('blob:') ? candidateImg : null;

    const parsedArea = areaSown.trim() ? parseFloat(areaSown) : null;

    try {
      const result = await generateLeafAdvisory({
        analysis_id: selectedDiagnosis.analysis_id,
        crop_name: selectedDiagnosis.crop_name,
        disease_name: selectedDiagnosis.disease_name,
        pest_name: selectedDiagnosis.pest_name,
        geolocation: geoVal,
        season: seasonVal,
        image_url: resolvedSpecimen,
        growth_stage: growthStage || null,
        onset_days: onsetDays || null,
        recent_weather: recentWeather || null,
        previous_treatment: previousTreatment || null,
        area_sown: parsedArea && !isNaN(parsedArea) && parsedArea > 0 ? parsedArea : null,
        area_unit: areaUnit,
        sowing_date: sowingDate.trim() || null,
        crop_variety: cropVariety.trim() || null,
        plant_part_affected: plantPartsAffected.length > 0 ? plantPartsAffected : null,
        irrigation_condition: irrigationCondition || null,
        severity_level: severityLevel || null,
        farmer_name: farmerName.trim() || null,
        farmer_phone: farmerPhone.trim() || null,
        farmer_notes: farmerNotes.trim() || null,
        gps_coordinates: gpsCoordinates.trim() || null,
      });

      // Guarantee specimen image is retained on the response object
      if (!result.image_url && resolvedSpecimen) {
        result.image_url = resolvedSpecimen;
      }

      setAdvisoryResult(result);
      setCurrentStep(3);
    } catch (err: any) {
      console.error('Error generating advisory:', err);
      setErrorMessage(err.response?.data?.detail || 'Failed to generate advisory. Please check connection and try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReset = () => {
    setSelectedDiagnosis(null);
    setSpecimenImageUrl(null);
    setGeolocation('');
    setSeason('');
    setGrowthStage('Vegetative');
    setOnsetDays('1-2 days ago (Acute)');
    setRecentWeather('Clear & Dry');
    setPreviousTreatment('None (First Spray)');
    setAreaSown('1.0');
    setSowingDate('');
    setCropVariety('');
    setPlantPartsAffected(['Leaf']);
    setIrrigationCondition('Normal');
    setSeverityLevel('Moderate (10-30%)');
    setFarmerName('');
    setFarmerPhone('');
    setFarmerNotes('');
    setGpsCoordinates('');
    setAdvisoryResult(null);
    setErrorMessage(null);
    setSpecimenImageError(false);
    setCurrentStep(1);
  };

  const filteredHistory = historyItems.filter((item) => {
    if (!searchHistory.trim()) return true;
    const q = searchHistory.toLowerCase();
    return (
      item.crop_name.toLowerCase().includes(q) ||
      (item.disease_name && item.disease_name.toLowerCase().includes(q)) ||
      (item.pest_name && item.pest_name.toLowerCase().includes(q)) ||
      item.analysis_id.toLowerCase().includes(q)
    );
  });

  // Unique categories for product filter
  const productCategories = React.useMemo(() => {
    if (!advisoryResult?.nacl_products) return ['ALL'];
    const cats = new Set<string>();
    advisoryResult.nacl_products.forEach((p) => {
      if (p.category) cats.add(p.category.toUpperCase());
    });
    return ['ALL', ...Array.from(cats)];
  }, [advisoryResult]);

  const filteredProducts = React.useMemo(() => {
    if (!advisoryResult?.nacl_products) return [];
    if (productCategoryFilter === 'ALL') return advisoryResult.nacl_products;
    return advisoryResult.nacl_products.filter(
      (p) => p.category?.toUpperCase() === productCategoryFilter
    );
  }, [advisoryResult, productCategoryFilter]);

  // Active specimen image in Step 3
  const rawSpecimen = advisoryResult?.image_url || specimenImageUrl || selectedDiagnosis?.image_url || null;
  const activeSpecimenImage = rawSpecimen && !rawSpecimen.startsWith('blob:') && !specimenImageError ? rawSpecimen : null;


  return (
    <div className="space-y-6 pb-16 w-full animate-in fade-in duration-300">
      {/* Header Banner - Full Width */}
      <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 sm:p-7 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="p-3.5 rounded-2xl bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0] shrink-0">
            <Stethoscope className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-extrabold text-warmgray-900 tracking-tight">
                Leaf Advisory & Agrochemical Intelligence
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0]">
                Senior Agronomist Engine
              </span>
            </div>
            <p className="text-xs text-warmgray-500 font-medium max-w-2xl">
              Synthesize precision treatment regimens with registered NACL Agrochemical remedies,
              seasonal weather spray windows, and verified Economic Threshold Levels (ETL).
            </p>
          </div>
        </div>

        {/* Step Indicator Pills */}
        <div className="flex items-center gap-2 self-start md:self-center bg-[#fbf9f5] border border-[#eae4dc] p-1 rounded-xl">
          <button
            type="button"
            onClick={() => currentStep > 1 && setCurrentStep(1)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              currentStep === 1
                ? 'bg-[#d96b27] text-white shadow-xs'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            1. Select Diagnosis
          </button>
          <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
          <button
            type="button"
            onClick={() => selectedDiagnosis && setCurrentStep(2)}
            disabled={!selectedDiagnosis}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all disabled:opacity-40 ${
              currentStep === 2
                ? 'bg-[#d96b27] text-white shadow-xs'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            2. Climate & Season
          </button>
          <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
          <div
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              currentStep === 3
                ? 'bg-[#d96b27] text-white shadow-xs'
                : 'text-slate-400'
            }`}
          >
            3. Advisory Dossier
          </div>
        </div>
      </div>

      {/* STEP 1: Select Historical Diagnosis Base */}
      {currentStep === 1 && (
        <div className="space-y-6">
          <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 sm:p-7 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#eae4dc]">
              <div>
                <h3 className="text-base font-extrabold text-slate-900">
                  Select a Diagnosis for Agronomist Advisory
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Pick any previously completed diagnostic run from Leaf Diagnosis or Leaf Scanner.
                </p>
              </div>

              {/* Filter Search */}
              <div className="relative w-full sm:w-72">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={searchHistory}
                  onChange={(e) => setSearchHistory(e.target.value)}
                  placeholder="Filter crop, disease, or pest..."
                  className="w-full bg-[#fbf9f5] border border-[#eae4dc] rounded-xl pl-9 pr-3 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#d96b27]/30 focus:border-[#d96b27]"
                />
              </div>
            </div>

            {loadingHistory ? (
              <div className="p-12 text-center text-slate-400 space-y-2">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto text-[#d96b27]" />
                <p className="text-xs">Loading recorded diagnoses from database...</p>
              </div>
            ) : filteredHistory.length === 0 ? (
              <div className="p-10 text-center border-2 border-dashed border-[#eae4dc] rounded-2xl space-y-3 bg-[#fbf9f5]">
                <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-slate-700">No matching diagnoses found</h4>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    {searchHistory
                      ? 'Try clearing your search query.'
                      : 'You do not have any saved diagnosis runs yet. Run a new diagnosis in Leaf Diagnosis first.'}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => navigate('/leaf-diagnosis')}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-[#d96b27] hover:bg-[#c55d1d] active:scale-[0.98] text-white rounded-xl text-xs font-bold shadow-sm transition-all cursor-pointer"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>Run First Diagnosis</span>
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredHistory.map((item) => (
                  <div
                    key={item.analysis_id}
                    onClick={() => handleSelectExistingDiagnosis(item)}
                    className="p-4 rounded-xl border border-[#eae4dc] bg-[#fbf9f5] hover:bg-white hover:border-[#d96b27] cursor-pointer transition-all shadow-xs hover:shadow-sm space-y-3 flex flex-col justify-between group"
                  >
                    <div>
                      <div className="flex items-center justify-between text-[11px] mb-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white border border-[#eae4dc] text-slate-600 font-mono">
                          {item.source === 'LEAF_DIAGNOSIS' ? 'Leaf Diagnosis' : 'Leaf Scanner'}
                        </span>
                        <span className="text-slate-400 font-mono text-[10px]">
                          {item.timestamp ? new Date(item.timestamp).toLocaleDateString() : 'Recent'}
                        </span>
                      </div>

                      <div className="flex items-start gap-3">
                        {item.image_url && !item.image_url.startsWith('blob:') && !failedHistoryImages[item.analysis_id] ? (
                          <div className="w-14 h-14 rounded-lg overflow-hidden border border-[#eae4dc] shrink-0 bg-slate-100">
                            <img
                              src={item.image_url}
                              alt={item.crop_name}
                              onError={() => setFailedHistoryImages((prev) => ({ ...prev, [item.analysis_id]: true }))}
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                            />
                          </div>
                        ) : (
                          <div className="w-14 h-14 rounded-lg border border-[#eae4dc] shrink-0 bg-slate-50 flex items-center justify-center text-slate-300">
                            <Sprout className="w-6 h-6 text-slate-400" />
                          </div>
                        )}

                        <div className="min-w-0 flex-1">
                          <h4 className="text-sm font-extrabold text-slate-900 group-hover:text-[#d96b27] transition-colors truncate">
                            {item.crop_name}
                          </h4>

                          <div className="mt-1 space-y-1 text-xs">
                            {item.disease_name && (
                              <div className="flex items-center gap-1.5 text-blue-700 font-medium">
                                <ShieldAlert className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                                <span className="truncate">{item.disease_name}</span>
                              </div>
                            )}
                            {item.pest_name && (
                              <div className="flex items-center gap-1.5 text-rose-700 font-medium">
                                <Bug className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                                <span className="truncate">{item.pest_name}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-[#eae4dc] flex items-center justify-between text-xs text-[#d96b27] font-bold group-hover:translate-x-0.5 transition-transform">
                      <span>Select for Advisory</span>
                      <ArrowRight className="w-4 h-4" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* STEP 2: Optional Geolocation & Season Input */}
      {currentStep === 2 && selectedDiagnosis && (
        <div className="space-y-6">
          {/* Selected Diagnosis Context Card */}
          <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              {specimenImageUrl ? (
                <div className="w-16 h-16 rounded-xl overflow-hidden border border-[#eae4dc] shrink-0 bg-slate-100 shadow-xs">
                  <img
                    src={specimenImageUrl}
                    alt={selectedDiagnosis.crop_name}
                    className="w-full h-full object-cover"
                  />
                </div>
              ) : (
                <div className="w-16 h-16 rounded-xl border border-[#eae4dc] shrink-0 bg-[#fdf3ed] flex items-center justify-center text-[#d96b27]">
                  <Sprout className="w-8 h-8" />
                </div>
              )}

              <div className="space-y-1">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                  Selected Diagnosis Base
                </span>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-black text-slate-900">
                    {selectedDiagnosis.crop_name}
                  </h3>
                  <span className="text-xs text-slate-400 font-mono">
                    ID: {selectedDiagnosis.analysis_id.slice(0, 10)}
                  </span>
                </div>
                <div className="flex flex-wrap gap-2 pt-1 text-xs">
                  {selectedDiagnosis.disease_name && (
                    <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 font-medium flex items-center gap-1">
                      <ShieldAlert className="w-3 h-3 text-blue-600" />
                      {selectedDiagnosis.disease_name}
                    </span>
                  )}
                  {selectedDiagnosis.pest_name && (
                    <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 font-medium flex items-center gap-1">
                      <Bug className="w-3 h-3 text-rose-600" />
                      {selectedDiagnosis.pest_name}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setCurrentStep(1)}
              className="text-xs text-slate-600 hover:text-[#d96b27] border border-[#eae4dc] hover:bg-[#fdf3ed] px-3.5 py-1.5 rounded-xl font-semibold transition-colors cursor-pointer"
            >
              Change Diagnosis
            </button>
          </div>

          {/* Farmer Problem — Quick Diagnosis Capture & Context Setup */}
          <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 sm:p-8 shadow-xs space-y-7">
            {/* Context & Zero-Hallucination Quality Banner */}
            <div className="p-4 bg-[#fdf3ed] border border-[#f5d5c0] rounded-xl flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-[#d96b27] shrink-0 mt-0.5" />
              <div className="text-xs text-warmgray-900 space-y-1">
                <span className="font-bold">Precision Diagnosis & Zero-Hallucination Agronomy:</span>
                <p className="text-warmgray-600 leading-relaxed">
                  To tailor bottle counts, dilution water, and safety timings (pollinator & harvest safety), select your field parameters below.
                </p>
                <p className="text-[#b95011] font-medium bg-[#fde8dc] px-2.5 py-1.5 rounded-lg border border-[#f5c6aa] mt-1">
                  💡 <strong>Unable to provide these inputs or unsure?</strong> No problem! You can select <strong>&quot;Not Sure / Standard&quot;</strong> on any item, or click <strong>&quot;Quick Generate (Standard Label Rate)&quot;</strong> below. Chemical remedies are strictly governed by your diagnosed crop and disease, so you will always receive 100% verified solutions!
                </p>
              </div>
            </div>

            {/* MANDATORY SECTION: Core Farmer Problem & Phenology */}
            <div className="space-y-6">
              <div className="flex items-center justify-between pb-2 border-b border-[#eae4dc]">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-[#d96b27] text-white">
                    <Activity className="w-4 h-4" />
                  </div>
                  <h4 className="text-sm font-extrabold text-slate-900">
                    Farmer Problem — Quick Diagnosis Intake
                  </h4>
                </div>
                <span className="text-[10px] uppercase font-extrabold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                  Required for Precision Guidance
                </span>
              </div>

              {/* 1. Crop Growth Stage */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                    <Sprout className="w-3.5 h-3.5 text-[#d96b27]" />
                    <span>1. Crop Growth Stage</span>
                  </label>
                  <span className="text-[10px] text-[#d96b27] font-semibold">
                    {growthStage === 'Flowering' ? '⚠️ Activates Pollinator Safety Gating' : growthStage === 'Fruiting / Maturation' ? '⏱️ Activates Pre-Harvest Interval (PHI)' : 'Growth Phenology'}
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  {[
                    { label: 'Seedling', icon: '🌱', desc: 'Tender nursery / early root establishment' },
                    { label: 'Vegetative', icon: '🌿', desc: 'Active tillering, branch & canopy flush' },
                    { label: 'Flowering', icon: '🌸', desc: 'Bud formation & active pollination (Bee safety)' },
                    { label: 'Fruiting / Maturation', icon: '🍎', desc: 'Pod/fruit set & ripening (Residue safety)' },
                    { label: 'Not Sure / Standard', icon: '❔', desc: 'Standard vegetative foliar dosage & safety' },
                  ].map((stage) => {
                    const isSel = growthStage === stage.label;
                    return (
                      <button
                        key={stage.label}
                        type="button"
                        onClick={() => setGrowthStage(stage.label)}
                        className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                          isSel
                            ? 'bg-[#fdf3ed] border-[#d96b27] shadow-xs'
                            : 'bg-[#fbf9f5] border-[#eae4dc] hover:bg-white hover:border-[#d96b27]/40'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm">{stage.icon}</span>
                          {isSel && <Check className="w-3.5 h-3.5 text-[#d96b27]" />}
                        </div>
                        <div className={`text-xs font-extrabold mt-1.5 ${isSel ? 'text-[#d96b27]' : 'text-slate-800'}`}>
                          {stage.label}
                        </div>
                        <div className="text-[10px] text-slate-500 mt-0.5 leading-snug">
                          {stage.desc}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 2. When First Observed (Onset) */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-[#d96b27]" />
                    <span>2. When First Observed (Symptom Onset)</span>
                  </label>
                  <span className="text-[10px] text-slate-400 font-medium">Infection Timeline</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {[
                    { label: '1-2 days ago (Acute)', desc: 'Immediate intervention window for maximum knockdown' },
                    { label: '3-7 days ago', desc: 'Secondary lesion growth & established infection' },
                    { label: '>1 week ago', desc: 'Chronic spread — triggers agronomist escalation' },
                    { label: 'Not Sure / Standard', desc: 'Standard curative/preventive foliar application' },
                  ].map((onset) => {
                    const isSel = onsetDays === onset.label;
                    return (
                      <button
                        key={onset.label}
                        type="button"
                        onClick={() => setOnsetDays(onset.label)}
                        className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                          isSel
                            ? 'bg-[#fdf3ed] border-[#d96b27] shadow-xs'
                            : 'bg-[#fbf9f5] border-[#eae4dc] hover:bg-white hover:border-[#d96b27]/40'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className={`text-xs font-extrabold ${isSel ? 'text-[#d96b27]' : 'text-slate-800'}`}>
                            {onset.label}
                          </span>
                          {isSel && <Check className="w-3.5 h-3.5 text-[#d96b27]" />}
                        </div>
                        <p className="text-[10px] text-slate-500 mt-1 leading-snug">
                          {onset.desc}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 3. Recent Climate & Weather */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                    <Droplets className="w-3.5 h-3.5 text-[#d96b27]" />
                    <span>3. Recent Microclimate & Weather (Last 48–72h)</span>
                  </label>
                  <span className="text-[10px] text-[#d96b27] font-semibold">
                    {recentWeather.includes('Rainy') ? '💧 Recommends Spreader-Sticker Tank Mix' : 'Rainfastness & Evaporation Calibration'}
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  {[
                    { label: 'Clear & Dry', icon: '☀️', desc: 'Low moisture, normal evapotranspiration' },
                    { label: 'Rainy / High Humidity', icon: '🌧️', desc: 'Wet foliage, requires non-ionic sticker adjuvant' },
                    { label: 'High Heat (>32°C)', icon: '🌡️', desc: 'Foliar scorch risk; early morning spray only' },
                    { label: 'Overcast / Windy', icon: '💨', desc: 'High drift risk; calibrate nozzle droplet size' },
                    { label: 'Not Sure / Normal', icon: '🌤️', desc: 'Standard early morning or evening foliar spray' },
                  ].map((w) => {
                    const isSel = recentWeather === w.label;
                    return (
                      <button
                        key={w.label}
                        type="button"
                        onClick={() => setRecentWeather(w.label)}
                        className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                          isSel
                            ? 'bg-[#fdf3ed] border-[#d96b27] shadow-xs'
                            : 'bg-[#fbf9f5] border-[#eae4dc] hover:bg-white hover:border-[#d96b27]/40'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm">{w.icon}</span>
                          {isSel && <Check className="w-3.5 h-3.5 text-[#d96b27]" />}
                        </div>
                        <div className={`text-xs font-extrabold mt-1.5 ${isSel ? 'text-[#d96b27]' : 'text-slate-800'}`}>
                          {w.label}
                        </div>
                        <div className="text-[10px] text-slate-500 mt-0.5 leading-snug">
                          {w.desc}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 4. Previous Treatment History */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-[#d96b27]" />
                    <span>4. Previous Chemical Treatment History</span>
                  </label>
                  <span className="text-[10px] text-[#d96b27] font-semibold">
                    {previousTreatment.includes('Ineffective') ? '⚠️ Activates Mode-of-Action Resistance Rotation' : 'Anti-Resistance Protocol'}
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {[
                    { label: 'None (First Spray)', desc: 'Initial curative/preventive spray on naive crop' },
                    { label: 'Already Sprayed - Ineffective', desc: 'Prior chemical failed. Strictly rotates active ingredient group' },
                    { label: 'Rotational Spray', desc: 'Sequential follow-up spray adhering to IPM rotation' },
                    { label: 'Not Sure / First Spray', desc: 'Standard baseline application adhering to label safety' },
                  ].map((treat) => {
                    const isSel = previousTreatment === treat.label;
                    return (
                      <button
                        key={treat.label}
                        type="button"
                        onClick={() => setPreviousTreatment(treat.label)}
                        className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                          isSel
                            ? 'bg-[#fdf3ed] border-[#d96b27] shadow-xs'
                            : 'bg-[#fbf9f5] border-[#eae4dc] hover:bg-white hover:border-[#d96b27]/40'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className={`text-xs font-extrabold ${isSel ? 'text-[#d96b27]' : 'text-slate-800'}`}>
                            {treat.label}
                          </span>
                          {isSel && <Check className="w-3.5 h-3.5 text-[#d96b27]" />}
                        </div>
                        <p className="text-[10px] text-slate-500 mt-1 leading-snug">
                          {treat.desc}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* LOCATION & SEASON CONTEXT SECTION */}
            <div className="space-y-5 pt-5 border-t border-[#eae4dc]">
              <div className="flex items-center justify-between pb-1">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-slate-800 text-white">
                    <Compass className="w-4 h-4" />
                  </div>
                  <h4 className="text-sm font-extrabold text-slate-900">
                    Geographic & Seasonal Climate Context
                  </h4>
                </div>
                <button
                  type="button"
                  onClick={handleDetectGps}
                  disabled={isDetectingGps}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-[#d96b27] hover:text-[#c55d1d] bg-[#fdf3ed] border border-[#f5d5c0] px-3 py-1 rounded-xl transition-all cursor-pointer disabled:opacity-50"
                >
                  <Locate className={`w-3.5 h-3.5 ${isDetectingGps ? 'animate-spin' : ''}`} />
                  <span>{isDetectingGps ? 'Detecting GPS...' : 'Auto-Detect GPS Location'}</span>
                </button>
              </div>

              {/* Geolocation Input & Quick Picks */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-[#d96b27]" />
                    <span>Agricultural Region or State</span>
                  </label>
                  {gpsCoordinates && (
                    <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      GPS: {gpsCoordinates}
                    </span>
                  )}
                </div>

                {optionsData?.suggested_regions && (
                  <div className="flex flex-wrap gap-1.5">
                    {optionsData.suggested_regions.map((reg) => (
                      <button
                        key={reg}
                        type="button"
                        onClick={() => setGeolocation(geolocation === reg ? '' : reg)}
                        className={`text-[11px] font-medium px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
                          geolocation === reg
                            ? 'bg-[#d96b27] text-white border-[#d96b27] shadow-xs'
                            : 'bg-[#fbf9f5] border-[#eae4dc] text-slate-700 hover:bg-white hover:border-[#d96b27]/40'
                        }`}
                      >
                        {reg}
                      </button>
                    ))}
                  </div>
                )}

                <input
                  type="text"
                  value={geolocation}
                  onChange={(e) => setGeolocation(e.target.value)}
                  placeholder="Or enter agricultural district (e.g. Nashik, Guntur, Bhatinda, Warangal)..."
                  className="w-full bg-[#fbf9f5] border border-[#eae4dc] rounded-xl px-3.5 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#d96b27]/30 focus:border-[#d96b27]"
                />
              </div>

              {/* Season Selection Cards */}
              <div className="space-y-2 pt-2">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-[#d96b27]" />
                  <span>Crop Season</span>
                </label>

                {optionsData?.suggested_seasons && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
                    {optionsData.suggested_seasons.map((s) => {
                      const isSelected = season === s.name;
                      return (
                        <div
                          key={s.name}
                          onClick={() => setSeason(isSelected ? '' : s.name)}
                          className={`p-3 rounded-xl border cursor-pointer transition-all ${
                            isSelected
                              ? 'bg-[#fdf3ed] border-[#d96b27] shadow-xs'
                              : 'bg-[#fbf9f5] border-[#eae4dc] hover:bg-white hover:border-[#d96b27]/40'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className={`text-xs font-bold ${isSelected ? 'text-[#d96b27]' : 'text-slate-800'}`}>
                              {s.name}
                            </span>
                            {isSelected && <Check className="w-3.5 h-3.5 text-[#d96b27]" />}
                          </div>
                          <p className="text-[11px] text-slate-500 mt-1 leading-snug">
                            {s.description}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* COLLAPSIBLE EXTENDED AGRONOMY PROFILE (Optional) */}
            <div className="pt-2 border-t border-[#eae4dc]">
              <button
                type="button"
                onClick={() => setShowExtendedFields(!showExtendedFields)}
                className="w-full py-3 px-4 rounded-xl bg-[#fbf9f5] hover:bg-[#fdf3ed] border border-[#eae4dc] text-xs font-bold text-slate-800 hover:text-[#d96b27] transition-all flex items-center justify-between cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-[#d96b27]" />
                  <span>Extended Agronomy & Acreage Dosage Calculator (Optional)</span>
                  <span className="text-[10px] font-normal text-slate-500">
                    (+ Acreage Bottle Packs, Sowing Date, Variety, Plant Parts, Notes)
                  </span>
                </div>
                {showExtendedFields ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {showExtendedFields && (
                <div className="mt-4 p-5 rounded-2xl border border-[#eae4dc] bg-[#fbf9f5] space-y-5 animate-in fade-in duration-200">
                  {/* Acreage & Dilution Feature Card */}
                  <div className="p-3 bg-white rounded-xl border border-[#f5d5c0] flex items-start gap-3">
                    <Beaker className="w-5 h-5 text-[#d96b27] shrink-0 mt-0.5" />
                    <div className="text-xs space-y-0.5">
                      <span className="font-extrabold text-[#d96b27]">Automatic Commercial Bottle & Dilution Calculator:</span>
                      <p className="text-slate-600">
                        Entering your field acreage computes total chemical volume (ml/gm), commercial pack bottle counts to buy at your local agrochemical dealer, and knapsack water dilution tanks!
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {/* Area Sown */}
                    <div className="space-y-1.5">
                      <label className="text-[11px] font-bold text-slate-700 uppercase">
                        Field Area Sown / Affected
                      </label>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          step="0.1"
                          min="0.1"
                          max="500"
                          value={areaSown}
                          onChange={(e) => setAreaSown(e.target.value)}
                          placeholder="e.g. 2.5"
                          className="w-full bg-white border border-[#eae4dc] rounded-xl px-3 py-2 text-xs text-slate-800 font-bold focus:outline-none focus:ring-2 focus:ring-[#d96b27]/30"
                        />
                        <select
                          value={areaUnit}
                          onChange={(e) => setAreaUnit(e.target.value as any)}
                          className="bg-white border border-[#eae4dc] rounded-xl px-2.5 py-2 text-xs text-slate-800 font-bold focus:outline-none"
                        >
                          <option value="acres">Acres</option>
                          <option value="hectares">Hectares</option>
                        </select>
                      </div>
                    </div>

                    {/* Sowing / Transplanting Date */}
                    <div className="space-y-1.5">
                      <label className="text-[11px] font-bold text-slate-700 uppercase">
                        Transplanting / Sowing Date
                      </label>
                      <input
                        type="date"
                        value={sowingDate}
                        onChange={(e) => setSowingDate(e.target.value)}
                        className="w-full bg-white border border-[#eae4dc] rounded-xl px-3 py-2 text-xs text-slate-800 font-medium focus:outline-none"
                      />
                    </div>

                    {/* Crop Variety / Hybrid */}
                    <div className="space-y-1.5">
                      <label className="text-[11px] font-bold text-slate-700 uppercase">
                        Crop Variety / Hybrid Name
                      </label>
                      <input
                        type="text"
                        value={cropVariety}
                        onChange={(e) => setCropVariety(e.target.value)}
                        placeholder="e.g. BT-2 Cotton, Pusa Basmati, US-7067"
                        className="w-full bg-white border border-[#eae4dc] rounded-xl px-3 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none"
                      />
                    </div>
                  </div>

                  {/* Plant Parts Affected */}
                  <div className="space-y-1.5">
                    <label className="text-[11px] font-bold text-slate-700 uppercase block">
                      Plant Parts Exhibiting Symptoms
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {['Leaf', 'Stem', 'Flower', 'Fruit / Pod', 'Root / Collar', 'Whole Plant Canopy'].map((part) => {
                        const isChecked = plantPartsAffected.includes(part);
                        return (
                          <button
                            key={part}
                            type="button"
                            onClick={() => {
                              if (isChecked) {
                                setPlantPartsAffected(plantPartsAffected.filter((p) => p !== part));
                              } else {
                                setPlantPartsAffected([...plantPartsAffected, part]);
                              }
                            }}
                            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer flex items-center gap-1.5 ${
                              isChecked
                                ? 'bg-[#d96b27] text-white border-[#d96b27]'
                                : 'bg-white border-[#eae4dc] text-slate-700 hover:border-[#d96b27]/40'
                            }`}
                          >
                            {isChecked ? <CheckSquare className="w-3.5 h-3.5" /> : <Square className="w-3.5 h-3.5" />}
                            <span>{part}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Irrigation Condition */}
                    <div className="space-y-1.5">
                      <label className="text-[11px] font-bold text-slate-700 uppercase block">
                        Irrigation & Soil Moisture Condition
                      </label>
                      <div className="grid grid-cols-3 gap-2">
                        {['Normal', 'Waterlogged / Flooded', 'Drought Stressed'].map((cond) => (
                          <button
                            key={cond}
                            type="button"
                            onClick={() => setIrrigationCondition(cond)}
                            className={`p-2 rounded-lg text-[11px] font-bold border transition-all ${
                              irrigationCondition === cond
                                ? 'bg-[#d96b27] text-white border-[#d96b27]'
                                : 'bg-white border-[#eae4dc] text-slate-700 hover:bg-slate-50'
                            }`}
                          >
                            {cond}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Severity Level */}
                    <div className="space-y-1.5">
                      <label className="text-[11px] font-bold text-slate-700 uppercase block">
                        Observed Severity Level
                      </label>
                      <div className="grid grid-cols-3 gap-2">
                        {['Mild (<10%)', 'Moderate (10-30%)', 'Severe (>30%)'].map((sev) => (
                          <button
                            key={sev}
                            type="button"
                            onClick={() => setSeverityLevel(sev)}
                            className={`p-2 rounded-lg text-[11px] font-bold border transition-all ${
                              severityLevel === sev
                                ? 'bg-[#d96b27] text-white border-[#d96b27]'
                                : 'bg-white border-[#eae4dc] text-slate-700 hover:bg-slate-50'
                            }`}
                          >
                            {sev}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Farmer Contact & Notes */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[11px] font-bold text-slate-700 uppercase">
                        Farmer Name & Phone (Optional)
                      </label>
                      <div className="grid grid-cols-2 gap-2">
                        <input
                          type="text"
                          value={farmerName}
                          onChange={(e) => setFarmerName(e.target.value)}
                          placeholder="Farmer Name"
                          className="bg-white border border-[#eae4dc] rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none"
                        />
                        <input
                          type="tel"
                          value={farmerPhone}
                          onChange={(e) => setFarmerPhone(e.target.value)}
                          placeholder="Phone Number"
                          className="bg-white border border-[#eae4dc] rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none"
                        />
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[11px] font-bold text-slate-700 uppercase">
                        Farmer Notes / Specific Field Observations
                      </label>
                      <textarea
                        rows={1}
                        value={farmerNotes}
                        onChange={(e) => setFarmerNotes(e.target.value)}
                        placeholder="Any additional observations (e.g. soil type, fertilizer applied, neighboring fields)..."
                        className="w-full bg-white border border-[#eae4dc] rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {errorMessage && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Action Buttons */}
            <div className="pt-6 border-t border-[#eae4dc] flex flex-col sm:flex-row items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => handleGenerateAdvisory(true)}
                disabled={isGenerating}
                className="w-full sm:w-auto px-5 py-2.5 bg-white border border-[#e5ded3] hover:bg-warmgray-50 text-warmgray-700 rounded-xl text-xs font-bold transition-colors shadow-xs cursor-pointer flex items-center justify-center gap-1.5"
              >
                <span>Quick Generate (Standard Label Rate)</span>
              </button>

              <button
                type="button"
                onClick={() => handleGenerateAdvisory(false)}
                disabled={isGenerating}
                className="w-full sm:w-auto px-6 py-2.5 bg-[#d96b27] hover:bg-[#c55d1d] active:scale-[0.98] disabled:bg-slate-300 text-white rounded-xl text-xs font-bold shadow-sm transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Synthesizing Precision Advisory...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Generate Agronomist Advisory & Dosage</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 3: Modern, Scannable Leaf Advisory Executive Report Dashboard */}
      {currentStep === 3 && advisoryResult && (
        <div className="space-y-6">
          {/* Executive Control & Status Strip */}
          <div className="bg-white rounded-2xl border border-[#eae4dc] p-4 sm:p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-3 flex-wrap">
              <div className="p-2.5 rounded-xl bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0]">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <h2 className="text-base font-extrabold text-slate-900">
                    Agronomic Advisory Dossier
                  </h2>
                  <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                    ID: {advisoryResult.advisory_id}
                  </span>
                  <span className="text-[11px] text-slate-400 font-medium">
                    • Generated: {new Date(advisoryResult.timestamp).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-600 mt-1 flex-wrap">
                  <span>Host Crop: <strong className="text-slate-900">{advisoryResult.crop_name}</strong></span>
                  {advisoryResult.disease_name && (
                    <span>• Pathology: <strong className="text-blue-700">{advisoryResult.disease_name}</strong></span>
                  )}
                  {advisoryResult.pest_name && (
                    <span>• Incursion: <strong className="text-rose-700">{advisoryResult.pest_name}</strong></span>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Action Buttons */}
            <div className="flex items-center gap-2 self-stretch md:self-auto justify-end">
              <button
                type="button"
                onClick={() => window.print()}
                className="px-3 py-2 bg-white border border-[#eae4dc] hover:bg-[#fbf9f5] text-slate-700 rounded-xl text-xs font-bold transition-colors flex items-center gap-1.5 shadow-xs cursor-pointer"
                title="Print or Save as PDF"
              >
                <Printer className="w-3.5 h-3.5 text-[#d96b27]" />
                <span>Export PDF</span>
              </button>

              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                className="px-3 py-2 bg-[#fdf3ed] hover:bg-[#fdeade] text-[#d96b27] border border-[#f5d5c0] rounded-xl text-xs font-bold transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <Sliders className="w-3.5 h-3.5" />
                <span>Tweak Climate</span>
              </button>

              <button
                type="button"
                onClick={handleReset}
                className="px-3 py-2 bg-[#d96b27] hover:bg-[#c55d1d] active:scale-[0.98] text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 shadow-xs cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>New Advisory</span>
              </button>
            </div>
          </div>

          {/* Escalation Alert Banner (High Risk Triggers) */}
          {advisoryResult.escalation_required && (
            <div className="p-4 bg-amber-50 border-2 border-amber-300 rounded-2xl flex items-start gap-3.5 shadow-xs animate-in fade-in duration-200">
              <div className="p-2 rounded-xl bg-amber-500 text-white shrink-0 mt-0.5 shadow-xs">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <h4 className="text-sm font-black text-amber-950 uppercase tracking-wide">
                    Agronomic Risk Escalation Required
                  </h4>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-200 text-amber-900 border border-amber-300">
                    High Priority Advisory
                  </span>
                </div>
                <p className="text-xs text-amber-900 leading-relaxed font-medium">
                  {advisoryResult.escalation_reason || 'Severe foliar progression or treatment failure requires immediate expert follow-up.'}
                </p>
              </div>
            </div>
          )}

          {/* Intake Telemetry Bar */}
          {advisoryResult.intake_summary && (
            <div className="bg-[#fbf9f5] border border-[#eae4dc] rounded-2xl p-4 shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-extrabold text-slate-700 uppercase tracking-wider text-[10px] flex items-center gap-1">
                  <Activity className="w-3.5 h-3.5 text-[#d96b27]" />
                  <span>Farmer Problem Telemetry:</span>
                </span>
                <span className="px-2 py-0.5 rounded-lg bg-white border border-[#eae4dc] font-semibold text-slate-800">
                  Stage: <strong>{advisoryResult.intake_summary.growth_stage}</strong>
                </span>
                <span className="px-2 py-0.5 rounded-lg bg-white border border-[#eae4dc] font-semibold text-slate-800">
                  Onset: <strong>{advisoryResult.intake_summary.onset_days}</strong>
                </span>
                <span className="px-2 py-0.5 rounded-lg bg-white border border-[#eae4dc] font-semibold text-slate-800">
                  Weather: <strong>{advisoryResult.intake_summary.recent_weather}</strong>
                </span>
                <span className="px-2 py-0.5 rounded-lg bg-white border border-[#eae4dc] font-semibold text-slate-800">
                  Prior Spray: <strong>{advisoryResult.intake_summary.previous_treatment}</strong>
                </span>
                {advisoryResult.intake_summary.area_sown && advisoryResult.intake_summary.area_sown !== 'Not specified' && (
                  <span className="px-2 py-0.5 rounded-lg bg-[#fdf3ed] border border-[#f5d5c0] font-bold text-[#d96b27]">
                    Acreage: {advisoryResult.intake_summary.area_sown}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Combination & Tank-Mix Guidance Section */}
          {advisoryResult.combination_guidance && (
            <div className="p-4 bg-gradient-to-r from-blue-50 via-[#fdf3ed] to-amber-50 border border-blue-200 rounded-2xl flex items-start gap-3.5 shadow-xs">
              <div className="p-2.5 rounded-xl bg-blue-600 text-white shrink-0 mt-0.5 shadow-xs">
                <FlaskConical className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <h4 className="text-sm font-extrabold text-slate-900">
                    Scientifically Verified Combination & Tank-Mix Strategy
                  </h4>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
                    Curative + Protective Synergy
                  </span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed font-medium">
                  {advisoryResult.combination_guidance}
                </p>
              </div>
            </div>
          )}

          {/* Acreage Bottle & Dilution Calculator Card */}
          {advisoryResult.area_calculation_summary && (
            <div className="p-4 bg-white border border-[#eae4dc] rounded-2xl flex items-start gap-3.5 shadow-xs">
              <div className="p-2.5 rounded-xl bg-emerald-600 text-white shrink-0 mt-0.5 shadow-xs">
                <Beaker className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <h4 className="text-sm font-extrabold text-slate-900">
                    Field Acreage Dilution & Total Packaging Requirement
                  </h4>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                    Dealer Purchase Ready
                  </span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed font-medium">
                  {advisoryResult.area_calculation_summary}
                </p>
              </div>
            </div>
          )}

          {/* 5-KPI Quick Metric Strip */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {/* KPI 1: Crop */}
            <div className="p-3.5 rounded-xl border border-[#eae4dc] bg-white shadow-xs space-y-1">
              <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                <span>Botanical Crop</span>
                <Sprout className="w-3.5 h-3.5 text-[#d96b27]" />
              </div>
              <div className="text-sm font-extrabold text-slate-900 truncate">
                {advisoryResult.crop_name}
              </div>
              <div className="text-[10px] text-emerald-600 font-medium">Cultivated Host Plant</div>
            </div>

            {/* KPI 2: Foliar Pathology */}
            <div className="p-3.5 rounded-xl border border-[#eae4dc] bg-white shadow-xs space-y-1">
              <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                <span>Foliar Disease</span>
                <ShieldAlert className="w-3.5 h-3.5 text-blue-600" />
              </div>
              <div className="text-sm font-extrabold text-slate-900 truncate">
                {advisoryResult.disease_name || 'None Diagnosed'}
              </div>
              <div className="text-[10px] text-blue-600 font-medium">
                {advisoryResult.disease_name ? 'EPPO Diagnostic Gated' : 'Pathology Negative'}
              </div>
            </div>

            {/* KPI 3: Pest Incursion */}
            <div className="p-3.5 rounded-xl border border-[#eae4dc] bg-white shadow-xs space-y-1">
              <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                <span>Arthropod Pest</span>
                <Bug className="w-3.5 h-3.5 text-rose-600" />
              </div>
              <div className="text-sm font-extrabold text-slate-900 truncate">
                {advisoryResult.pest_name || 'No Pest Incursion'}
              </div>
              <div className="text-[10px] text-rose-600 font-medium">
                {advisoryResult.pest_name ? 'IP102 Benchmark Validated' : 'Foliage Pest-Free'}
              </div>
            </div>

            {/* KPI 4: Climate Risk */}
            <div className="p-3.5 rounded-xl border border-[#eae4dc] bg-white shadow-xs space-y-1">
              <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                <span>Regional Risk</span>
                <Compass className="w-3.5 h-3.5 text-amber-600" />
              </div>
              <div className="text-sm font-extrabold text-slate-900 flex items-center gap-1.5">
                <span
                  className={`inline-block w-2 h-2 rounded-full ${
                    advisoryResult.seasonal_risk.disease_pressure_level === 'HIGH'
                      ? 'bg-rose-500'
                      : advisoryResult.seasonal_risk.disease_pressure_level === 'LOW'
                      ? 'bg-emerald-500'
                      : 'bg-amber-500'
                  }`}
                />
                <span>{advisoryResult.seasonal_risk.disease_pressure_level} Level</span>
              </div>
              <div className="text-[10px] text-slate-500 truncate">
                {advisoryResult.geolocation || 'General Zone'}
              </div>
            </div>

            {/* KPI 5: NACL Remedies */}
            <div className="p-3.5 rounded-xl border border-[#eae4dc] bg-white shadow-xs space-y-1 col-span-2 md:col-span-1">
              <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                <span>NACL Catalog</span>
                <Layers className="w-3.5 h-3.5 text-[#d96b27]" />
              </div>
              <div className="text-sm font-extrabold text-slate-900">
                {advisoryResult.nacl_products.length} Products
              </div>
              <div className="text-[10px] text-[#d96b27] font-medium">Verified Active Registrations</div>
            </div>
          </div>

          {/* SECTION A: Pest & Pathology Identification Dossier (Featuring Actual Leaf Specimen) */}
          <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 sm:p-7 shadow-xs space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-[#eae4dc]">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-rose-50 border border-rose-200 text-rose-600">
                  <Bug className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-slate-900">
                    Pest & Pathology Identification Dossier
                  </h3>
                  <p className="text-xs text-slate-500">
                    Specimen visual record and quantitative Economic Threshold Level (ETL) comparison.
                  </p>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0]">
                Diagnostic Evidence
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Column 1: Actual Leaf Specimen Under Inspection */}
              <div className="lg:col-span-5 space-y-3">
                <div className="relative rounded-2xl overflow-hidden border border-[#eae4dc] bg-slate-950 aspect-4/3 group shadow-xs flex items-center justify-center">
                  {activeSpecimenImage ? (
                    <>
                      <img
                        src={activeSpecimenImage}
                        alt="Diagnosed Foliar Specimen"
                        onError={() => setSpecimenImageError(true)}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                      />
                      {/* Floating Metadata Pill */}
                      <div className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-md px-2.5 py-1 rounded-lg border border-white/20 text-white text-[10px] font-bold flex items-center gap-1.5 shadow-sm">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                        <span>Actual Uploaded Specimen</span>
                      </div>

                      {/* Enlarge Button */}
                      <button
                        type="button"
                        onClick={() => setIsImageModalOpen(true)}
                        className="absolute bottom-3 right-3 bg-slate-900/80 hover:bg-[#d96b27] backdrop-blur-md p-2 rounded-lg border border-white/20 text-white text-xs font-bold transition-colors cursor-pointer shadow-sm flex items-center gap-1"
                        title="Click to expand high-resolution specimen"
                      >
                        <Maximize2 className="w-3.5 h-3.5" />
                        <span className="text-[10px]">Inspect Specimen</span>
                      </button>

                      {/* Diagnosed Target Badge Overlay */}
                      <div className="absolute bottom-3 left-3 bg-slate-900/85 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/20 text-white space-y-0.5">
                        <div className="text-[9px] uppercase tracking-wider text-slate-300 font-bold">
                          Diagnosed Condition
                        </div>
                        <div className="text-xs font-black text-[#d96b27] flex items-center gap-1">
                          <span>{advisoryResult.pest_name || advisoryResult.disease_name || 'Healthy Specimen'}</span>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="p-8 text-center space-y-2 text-slate-400">
                      <Sprout className="w-10 h-10 text-slate-600 mx-auto" />
                      <div className="text-xs font-bold text-slate-300">Specimen Visual Record</div>
                      <p className="text-[11px] text-slate-500 max-w-xs mx-auto">
                        Specimen metadata preserved in diagnostic audit log. Run next scan with image upload for instant visual inspection.
                      </p>
                    </div>
                  )}
                </div>

                <div className="p-3 bg-[#fbf9f5] border border-[#eae4dc] rounded-xl flex items-center justify-between text-xs text-slate-600">
                  <span className="font-semibold">Host Crop: <strong>{advisoryResult.crop_name}</strong></span>
                  <span className="font-mono text-[11px] text-slate-500">
                    Source: {selectedDiagnosis?.source || 'Diagnostic Pipeline'}
                  </span>
                </div>
              </div>

              {/* Column 2: Diagnostic Dossier & Economic Threshold Comparison (ETL / EIL) */}
              <div className="lg:col-span-7 space-y-4">
                {/* Target Organism Profile Card */}
                {(() => {
                  const hasPest = Boolean(advisoryResult.pest_name);
                  const hasDisease = Boolean(advisoryResult.disease_name);
                  const pestLower = (advisoryResult.pest_name || '').toLowerCase();
                  const diseaseLower = (advisoryResult.disease_name || '').toLowerCase();

                  // Dynamic primary symptom
                  let symptomDesc = 'Photosynthetically Uncompromised Foliage';
                  if (pestLower) {
                    if (pestLower.includes('beetle') || pestLower.includes('caterpillar') || pestLower.includes('worm') || pestLower.includes('moth') || pestLower.includes('grasshopper') || pestLower.includes('weevil')) {
                      symptomDesc = 'Foliar Defoliation & Tissue Skeletonization';
                    } else if (pestLower.includes('aphid') || pestLower.includes('fly') || pestLower.includes('hopper') || pestLower.includes('mite') || pestLower.includes('thrip') || pestLower.includes('bug')) {
                      symptomDesc = 'Cell-Sap Depletion, Chlorosis & Honeydew Excretion';
                    } else if (pestLower.includes('borer')) {
                      symptomDesc = 'Internal Vascular Tunneling & Terminal Shoot Wilting';
                    } else {
                      symptomDesc = `Foliar Tissue Feeding & Canopy Depletion (${advisoryResult.pest_name})`;
                    }
                  } else if (diseaseLower) {
                    if (diseaseLower.includes('mildew') || diseaseLower.includes('mold') || diseaseLower.includes('rust') || diseaseLower.includes('blight') || diseaseLower.includes('spot') || diseaseLower.includes('rot')) {
                      symptomDesc = 'Pathogen Sporulation, Chlorotic Halos & Necrotic Lesions';
                    } else if (diseaseLower.includes('virus') || diseaseLower.includes('mosaic') || diseaseLower.includes('curl')) {
                      symptomDesc = 'Systemic Foliar Mosaics, Curling & Cellular Stunting';
                    } else {
                      symptomDesc = `Foliar Pathology & Necrotic Discoloration (${advisoryResult.disease_name})`;
                    }
                  }

                  // Dynamic vulnerable stage
                  const vulnerableStage = hasPest
                    ? 'Early Instar Larvae & Actively Feeding Adults'
                    : hasDisease
                    ? 'Initial Spore Germination & Epiphytic Growth'
                    : 'Vegetative Canopy & Bud Formation';

                  // Dynamic damage velocity
                  const damageVelocity = advisoryResult.seasonal_risk.disease_pressure_level === 'HIGH'
                    ? 'Accelerated Foliar Spread (High Humidity Risk)'
                    : (hasPest || hasDisease)
                    ? 'Progressive Foliar Area Reduction'
                    : 'Stable Botanical Baseline';

                  // Dynamic threat status
                  const isThreatActive = hasPest || hasDisease || advisoryResult.seasonal_risk.disease_pressure_level === 'HIGH';

                  // Dynamic ETL guideline
                  let etlGuideline = '';
                  if (hasPest && hasDisease) {
                    etlGuideline = `For ${advisoryResult.crop_name}, dual pressure is detected: foliar chemical intervention is triggered when ${advisoryResult.pest_name} density exceeds 2–3 active specimens per plant cluster, or when ${advisoryResult.disease_name} lesions exceed 5% of canopy surface.`;
                  } else if (hasPest) {
                    etlGuideline = `For ${advisoryResult.crop_name}, chemical intervention is triggered when foliar damage reaches 5%–10% or pest density exceeds 2–3 active ${advisoryResult.pest_name} specimens per plant cluster.`;
                  } else if (hasDisease) {
                    etlGuideline = `For ${advisoryResult.crop_name}, protective and curative treatment for ${advisoryResult.disease_name} is justified upon initial symptom manifestation (1–2 lesions per 10 plants) to prevent irreversible harvest loss.`;
                  } else {
                    etlGuideline = `For ${advisoryResult.crop_name}, foliar symptoms are currently below the Economic Threshold Level (ETL). Maintain periodic field monitoring; prophylactic chemical spraying is not economically warranted.`;
                  }

                  // Dynamic EIL rationale
                  let eilRationale = '';
                  const targetName = advisoryResult.pest_name || advisoryResult.disease_name;
                  if (targetName) {
                    eilRationale = `The cost of targeted agrochemical application for ${targetName} is significantly lower than projected 18%–35% yield depression resulting from unchecked foliar depletion. Timely curative application is economically justified.`;
                  } else {
                    eilRationale = `Current foliar density is well below the Economic Injury Level. Avoiding premature spraying protects beneficial predatory insects and eliminates unnecessary input cost.`;
                  }

                  return (
                    <>
                      <div className="p-4 rounded-xl border border-[#eae4dc] bg-[#fbf9f5] space-y-3">
                        <div className="flex items-center justify-between flex-wrap gap-2">
                          <div>
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                              Target Organism Classification
                            </span>
                            <h4 className="text-base font-black text-slate-900">
                              {advisoryResult.pest_name || advisoryResult.disease_name || 'Foliar Condition Monitored'}
                            </h4>
                          </div>

                          <span
                            className={`px-2.5 py-1 rounded-lg text-xs font-bold border ${
                              isThreatActive
                                ? 'bg-rose-50 text-rose-700 border-rose-200'
                                : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            }`}
                          >
                            {isThreatActive ? 'Threat Status: Active Treatment Warranted' : 'Threat Status: Sub-Threshold (Monitoring Mode)'}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 pt-1 text-xs">
                          <div className="p-2.5 bg-white border border-[#eae4dc] rounded-lg">
                            <span className="text-[10px] font-bold text-slate-400 block uppercase">Primary Symptom</span>
                            <span className="font-bold text-slate-800">{symptomDesc}</span>
                          </div>

                          <div className="p-2.5 bg-white border border-[#eae4dc] rounded-lg">
                            <span className="text-[10px] font-bold text-slate-400 block uppercase">Vulnerable Stage</span>
                            <span className="font-bold text-slate-800">{vulnerableStage}</span>
                          </div>

                          <div className="p-2.5 bg-white border border-[#eae4dc] rounded-lg col-span-2 sm:col-span-1">
                            <span className="text-[10px] font-bold text-slate-400 block uppercase">Damage Velocity</span>
                            <span className={`font-bold ${isThreatActive ? 'text-rose-700' : 'text-emerald-700'}`}>
                              {damageVelocity}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Economic Threshold Level (ETL) vs Economic Injury Level (EIL) */}
                      <div className="p-4 rounded-xl border border-[#f5d5c0] bg-[#fdf3ed] space-y-3">
                        <div className="flex items-center justify-between flex-wrap gap-2">
                          <div className="flex items-center gap-2">
                            <Scale className="w-4 h-4 text-[#d96b27]" />
                            <h4 className="text-xs font-extrabold uppercase tracking-wider text-warmgray-900">
                              Economic Threshold Level (ETL) & Intervention Decision
                            </h4>
                          </div>
                          <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                            isThreatActive
                              ? 'bg-white text-[#d96b27] border-[#f5d5c0]'
                              : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                          }`}>
                            {isThreatActive ? 'IPM Action Gate: AT / EXCEEDING THRESHOLD' : 'IPM Action Gate: SUB-THRESHOLD'}
                          </span>
                        </div>

                        <p className="text-xs text-warmgray-700 leading-relaxed">
                          <strong>Economic Threshold (ETL) Guideline:</strong> {etlGuideline}
                        </p>

                        {/* Quantitative Progress Gauge */}
                        <div className="space-y-1.5 pt-1">
                          <div className="flex items-center justify-between text-[11px] font-bold">
                            <span className="text-slate-600">Current Field Threat Severity</span>
                            <span className={isThreatActive ? 'text-rose-700 font-extrabold' : 'text-emerald-700 font-extrabold'}>
                              {isThreatActive ? 'Above Economic Threshold (Action Warranted)' : 'Within Acceptable Baseline (Monitoring)'}
                            </span>
                          </div>
                          <div className="w-full h-3 bg-white rounded-full overflow-hidden border border-[#eae4dc] flex">
                            <div className="w-1/3 bg-emerald-400" title="Safe / Sub-threshold" />
                            <div className="w-1/3 bg-amber-400" title="Economic Threshold (ETL)" />
                            <div className="w-1/3 bg-rose-500 relative" title="Economic Injury Level (EIL)">
                              {isThreatActive && <div className="absolute inset-0 bg-white/20 animate-pulse" />}
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                            <span className={!isThreatActive ? 'font-bold text-emerald-600' : ''}>▲ Low Baseline</span>
                            <span className="font-bold text-amber-600">▲ ETL (Intervene Here)</span>
                            <span className={isThreatActive ? 'font-bold text-rose-600' : ''}>▲ EIL (Economic Loss)</span>
                          </div>
                        </div>

                        <div className="p-2.5 rounded-lg bg-white border border-[#f5d5c0] text-[11px] text-warmgray-800 leading-snug">
                          <strong className="text-[#d96b27]">Economic Injury Level (EIL) Rationale:</strong> {eilRationale}
                        </div>
                      </div>
                    </>
                  );
                })()}
              </div>
            </div>
          </div>

          {/* SECTION B: Spraying Time Windows & Environmental Feasibility */}
          <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 sm:p-7 shadow-xs space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-[#eae4dc]">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-[#fdf3ed] border border-[#f5d5c0] text-[#d96b27]">
                  <Clock className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-slate-900">
                    Optimal Spraying Time Windows & Meteorology
                  </h3>
                  <p className="text-xs text-slate-500">
                    Weather spray windows calibrated for maximum systemic absorption and zero drift.
                  </p>
                </div>
              </div>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                  advisoryResult.seasonal_risk.disease_pressure_level === 'HIGH'
                    ? 'bg-rose-100 text-rose-800 border border-rose-200'
                    : advisoryResult.seasonal_risk.disease_pressure_level === 'LOW'
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                    : 'bg-amber-100 text-amber-800 border border-amber-200'
                }`}
              >
                {advisoryResult.seasonal_risk.disease_pressure_level} Climate Risk
              </span>
            </div>

            {/* Daily Spray Window Timeline Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
              {/* Window 1: Morning (Recommended) */}
              <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
                    <Sun className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Morning Window (Primary)</span>
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-emerald-600 text-white">
                    OPTIMAL
                  </span>
                </div>
                <div className="text-base font-black text-emerald-950 font-mono">
                  06:00 AM – 09:30 AM
                </div>
                <p className="text-xs text-emerald-800 leading-snug">
                  Calm winds (&lt; 8 km/h), high humidity, stomatal opening, and minimal solar photodecomposition.
                </p>
              </div>

              {/* Window 2: Midday (Prohibited) */}
              <div className="p-4 rounded-xl border border-rose-200 bg-rose-50/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-rose-800 uppercase tracking-wider flex items-center gap-1">
                    <Thermometer className="w-3.5 h-3.5 text-rose-600" />
                    <span>Midday Window (Strictly Avoid)</span>
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-rose-600 text-white">
                    PROHIBITED
                  </span>
                </div>
                <div className="text-base font-black text-rose-950 font-mono">
                  11:00 AM – 03:30 PM
                </div>
                <p className="text-xs text-rose-800 leading-snug">
                  High thermal evaporation causes foliar phytotoxicity scorch and drift; active beneficial pollinator foraging.
                </p>
              </div>

              {/* Window 3: Evening (Secondary) */}
              <div className="p-4 rounded-xl border border-[#f5d5c0] bg-[#fdf3ed]/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-[#d96b27] uppercase tracking-wider flex items-center gap-1">
                    <Wind className="w-3.5 h-3.5 text-[#d96b27]" />
                    <span>Evening Window (Secondary)</span>
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-[#d96b27] text-white">
                    FAVORABLE
                  </span>
                </div>
                <div className="text-base font-black text-warmgray-900 font-mono">
                  04:30 PM – 07:00 PM
                </div>
                <p className="text-xs text-warmgray-700 leading-snug">
                  Decreasing ambient temperatures and calming breeze. Prolonged dew ensures extended chemical uptake.
                </p>
              </div>
            </div>

            {/* Meteorological Parameters Strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-[#fbf9f5] border border-[#eae4dc]">
              <div className="space-y-0.5">
                <div className="flex items-center gap-1 text-[10px] font-bold text-slate-400 uppercase">
                  <Thermometer className="w-3.5 h-3.5 text-[#d96b27]" />
                  <span>Ambient Temp</span>
                </div>
                <div className="text-xs font-black text-slate-800 font-mono">20°C – 28°C</div>
                <div className="text-[10px] text-slate-500">Avoid &gt; 32°C (scorch risk)</div>
              </div>

              <div className="space-y-0.5">
                <div className="flex items-center gap-1 text-[10px] font-bold text-slate-400 uppercase">
                  <Droplets className="w-3.5 h-3.5 text-blue-500" />
                  <span>Relative Humidity</span>
                </div>
                <div className="text-xs font-black text-slate-800 font-mono">60% – 85% RH</div>
                <div className="text-[10px] text-slate-500">Aids droplet droplet spread</div>
              </div>

              <div className="space-y-0.5">
                <div className="flex items-center gap-1 text-[10px] font-bold text-slate-400 uppercase">
                  <Wind className="w-3.5 h-3.5 text-slate-500" />
                  <span>Wind Velocity</span>
                </div>
                <div className="text-xs font-black text-slate-800 font-mono">&lt; 10 km/h (Calm)</div>
                <div className="text-[10px] text-slate-500">Prevents off-target drift</div>
              </div>

              <div className="space-y-0.5">
                <div className="flex items-center gap-1 text-[10px] font-bold text-slate-400 uppercase">
                  <Sun className="w-3.5 h-3.5 text-amber-500" />
                  <span>Rainfastness</span>
                </div>
                <div className="text-xs font-black text-slate-800 font-mono">3 – 4 Hours Rain-Free</div>
                <div className="text-[10px] text-slate-500">Guarantees leaf bonding</div>
              </div>
            </div>

            {/* Tailored Context Advice */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-[#fbf9f5] border border-[#eae4dc] rounded-xl space-y-1.5">
                <div className="text-[11px] uppercase font-bold text-slate-500 tracking-wider">
                  Environmental & Climate Factors ({advisoryResult.seasonal_risk.season_name})
                </div>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {advisoryResult.seasonal_risk.climate_factors}
                </p>
              </div>

              <div className="p-4 bg-[#fdf3ed] border border-[#f5d5c0] rounded-xl space-y-1.5">
                <div className="text-[11px] uppercase font-bold text-[#d96b27] tracking-wider">
                  Agronomic Spray Window Counsel
                </div>
                <p className="text-xs text-warmgray-900 leading-relaxed">
                  {advisoryResult.seasonal_risk.weather_spray_window_advice}
                </p>
              </div>
            </div>
          </div>

          {/* SECTION C: Verified NACL Product Catalog (Interactive Product Table & Cards) */}
          <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 sm:p-7 shadow-xs space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#eae4dc]">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-[#fdf3ed] border border-[#f5d5c0] text-[#d96b27]">
                  <Layers className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-slate-900">
                    Verified Remedies from NACL Product Catalog
                  </h3>
                  <p className="text-xs text-slate-500">
                    Statutory registered formulations ranked by beneficial efficacy, host suitability, and prescribed field dosage.
                  </p>
                </div>
              </div>

              {/* View Toggle & Filter Controls */}
              <div className="flex items-center gap-2 flex-wrap">
                {/* Category Pills */}
                <div className="flex items-center gap-1 bg-[#fbf9f5] border border-[#eae4dc] p-1 rounded-xl">
                  {productCategories.map((cat) => (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => setProductCategoryFilter(cat)}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all cursor-pointer ${
                        productCategoryFilter === cat
                          ? 'bg-[#d96b27] text-white shadow-xs'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                {/* View Switcher: Table vs Cards */}
                <div className="flex items-center bg-[#fbf9f5] border border-[#eae4dc] p-1 rounded-xl">
                  <button
                    type="button"
                    onClick={() => setProductViewMode('table')}
                    className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
                      productViewMode === 'table'
                        ? 'bg-white text-[#d96b27] shadow-xs'
                        : 'text-slate-400 hover:text-slate-700'
                    }`}
                    title="Table View"
                  >
                    <TableIcon className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setProductViewMode('cards')}
                    className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
                      productViewMode === 'cards'
                        ? 'bg-white text-[#d96b27] shadow-xs'
                        : 'text-slate-400 hover:text-slate-700'
                    }`}
                    title="Grid Card View"
                  >
                    <LayoutGrid className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {filteredProducts.length === 0 ? (
              advisoryResult.nacl_products.length === 0 ? (
                <div className="p-8 text-center bg-[#fdf3ed] border-2 border-[#f5d5c0] rounded-2xl space-y-3">
                  <div className="w-12 h-12 rounded-2xl bg-[#d96b27] text-white flex items-center justify-center mx-auto shadow-xs">
                    <ShieldCheck className="w-6 h-6" />
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-sm font-black text-slate-900">
                      Zero-Hallucination Safety Guarantee: No Unverified Chemicals
                    </h4>
                    <p className="text-xs text-warmgray-700 max-w-xl mx-auto leading-relaxed">
                      No registered NACL chemical product in our catalog is specifically licensed for{' '}
                      <strong>{advisoryResult.disease_name || advisoryResult.pest_name || 'this condition'}</strong> on{' '}
                      <strong>{advisoryResult.crop_name}</strong>. To protect your crop health, prevent phytotoxicity, and avoid financial loss, our system strictly avoids recommending unverified or off-label chemicals. Please follow the verified cultural, biological, and sanitary remedies detailed below.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center bg-[#fbf9f5] border border-[#eae4dc] rounded-xl space-y-2 text-slate-500">
                  <Layers className="w-8 h-8 text-slate-400 mx-auto" />
                  <div className="text-xs font-bold text-slate-700">No products matching the selected filter</div>
                  <p className="text-[11px] text-slate-400">
                    Try switching back to 'ALL' to view all registered formulations.
                  </p>
                </div>
              )
            ) : productViewMode === 'table' ? (
              /* MODERN PRODUCT TABLE VIEW WITH ZERO-HALLUCINATION & ACREAGE DOSAGE */
              <div className="overflow-x-auto rounded-xl border border-[#eae4dc] shadow-xs">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-[#fbf9f5] border-b border-[#eae4dc] text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                      <th className="py-3 px-4">Product & Category</th>
                      <th className="py-3 px-3">Active Chemical</th>
                      <th className="py-3 px-3">Beneficial Rank</th>
                      <th className="py-3 px-3">Standard Statutory Label Rate</th>
                      <th className="py-3 px-4">Field Acreage Requirement & Bottles</th>
                      <th className="py-3 px-3">Safety & Combination</th>
                      <th className="py-3 px-4 text-right">Official Link</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#eae4dc] bg-white">
                    {filteredProducts.map((prod, idx) => (
                      <tr key={prod.product_id} className="hover:bg-[#fdf3ed]/40 transition-colors">
                        <td className="py-3.5 px-4 font-extrabold text-slate-900">
                          <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-[#d96b27]" />
                            <span>{prod.product_name}</span>
                          </div>
                          <span className="mt-1 inline-block px-1.5 py-0.5 rounded text-[9px] font-bold bg-[#fdeade] text-[#d96b27]">
                            {prod.category}
                          </span>
                        </td>
                        <td className="py-3.5 px-3 text-slate-600 italic text-[11px]">
                          {prod.active_ingredient || 'Formulated Agrochemical'}
                        </td>
                        <td className="py-3.5 px-3">
                          {prod.benefit_badge ? (
                            <span className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full font-bold border ${
                              prod.efficacy_rank === 1
                                ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                                : prod.efficacy_rank === 2
                                ? 'bg-blue-100 text-blue-800 border-blue-200'
                                : prod.efficacy_rank === 3
                                ? 'bg-amber-100 text-amber-800 border-amber-200'
                                : 'bg-slate-100 text-slate-700 border-slate-200'
                            }`} title={prod.benefit_reason}>
                              {prod.efficacy_rank === 1 && <Sparkles className="w-3 h-3 text-emerald-600" />}
                              <span>{prod.benefit_badge}</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full font-bold border bg-emerald-100 text-emerald-800 border-emerald-300">
                              <Sparkles className="w-3 h-3 text-emerald-600" />
                              <span>Rank #{idx + 1}</span>
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-3 font-semibold text-slate-800 text-[11px]">
                          <span className="px-2 py-1 rounded-md bg-[#fbf9f5] border border-[#eae4dc] font-mono block">
                            {prod.standard_label_dosage || prod.recommended_dosage || 'Refer to Product Label'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-bold text-[#d96b27]">
                          {prod.calculated_total_dosage ? (
                            <div className="space-y-1">
                              <div className="text-xs font-black text-[#d96b27]">
                                Total Needed: {prod.calculated_total_dosage}
                              </div>
                              {prod.calculated_bottles && (
                                <div className="text-[10px] text-slate-700 font-medium">
                                  Packs: <strong className="text-slate-900">{prod.calculated_bottles}</strong>
                                </div>
                              )}
                              {prod.calculated_total_water && (
                                <div className="text-[10px] text-blue-700 font-medium">
                                  {prod.calculated_total_water}
                                </div>
                              )}
                            </div>
                          ) : (
                            <span className="text-[11px] text-slate-500 font-medium">
                              {prod.recommended_dosage || 'Refer to label'}
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-3">
                          <div className="space-y-1 text-[10px]">
                            {prod.bee_toxicity_warning && (
                              <span className="inline-block px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-bold">
                                🐝 Evening Spray (Bee Safe)
                              </span>
                            )}
                            <div className="flex items-center gap-1 text-slate-500">
                              {prod.phi_days && <span className="font-semibold">PHI: {prod.phi_days}d</span>}
                              {prod.rei_hours && <span className="font-semibold">• REI: {prod.rei_hours}h</span>}
                            </div>
                            {prod.combination_partner && (
                              <div className="text-[10px] text-blue-700 italic max-w-xs truncate" title={prod.combination_partner}>
                                Mix: {prod.combination_partner}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <a
                            href={prod.product_url || 'https://naclind.com/products/'}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl bg-white border border-[#eae4dc] hover:border-[#d96b27] text-slate-700 hover:text-[#d96b27] font-bold text-[11px] transition-all shadow-xs"
                          >
                            <span>Official Page</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              /* MODERN PRODUCT CARD GRID VIEW WITH DOSAGE & COMBINATION */
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredProducts.map((prod, idx) => (
                  <div
                    key={prod.product_id}
                    className="p-4 rounded-2xl border border-[#eae4dc] bg-[#fbf9f5] hover:bg-white hover:border-[#d96b27] transition-all shadow-xs flex flex-col justify-between space-y-3.5 group"
                  >
                    <div className="space-y-2.5">
                      <div className="flex items-center justify-between text-[11px] gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#fdeade] text-[#d96b27]">
                          {prod.category}
                        </span>
                        {prod.benefit_badge ? (
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border flex items-center gap-1 ${
                            prod.efficacy_rank === 1
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                              : prod.efficacy_rank === 2
                              ? 'bg-blue-50 text-blue-700 border-blue-200'
                              : 'bg-white text-slate-600 border-slate-200'
                          }`}>
                            {prod.efficacy_rank === 1 && <Sparkles className="w-2.5 h-2.5 text-emerald-600" />}
                            <span>{prod.benefit_badge}</span>
                          </span>
                        ) : (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full border bg-emerald-100 text-emerald-800 border-emerald-300">
                            Rank #{idx + 1}
                          </span>
                        )}
                      </div>

                      <div>
                        <h4 className="text-base font-black text-slate-900 group-hover:text-[#d96b27] transition-colors">
                          {prod.product_name}
                        </h4>
                        {prod.active_ingredient && (
                          <p className="text-xs text-slate-500 italic mt-0.5">
                            {prod.active_ingredient}
                          </p>
                        )}
                      </div>

                      {/* Standard Statutory Label Rate */}
                      <div className="p-2.5 bg-white border border-[#eae4dc] rounded-xl text-xs space-y-0.5">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">
                          Standard Statutory Label Rate
                        </span>
                        <span className="font-bold text-[#d96b27] text-xs font-mono">
                          {prod.standard_label_dosage || prod.recommended_dosage || 'Refer to product label'}
                        </span>
                      </div>

                      {/* Field Acreage Calculation (if computed) */}
                      {prod.calculated_total_dosage && (
                        <div className="p-2.5 bg-[#fdf3ed] border border-[#f5d5c0] rounded-xl text-xs space-y-1">
                          <div className="flex items-center justify-between text-[10px] uppercase font-extrabold text-[#d96b27]">
                            <span>Field Acreage Requirement</span>
                            <Beaker className="w-3 h-3 text-[#d96b27]" />
                          </div>
                          <div className="text-xs font-black text-slate-900">
                            Total Volume: {prod.calculated_total_dosage}
                          </div>
                          {prod.calculated_bottles && (
                            <div className="text-[11px] text-slate-700 font-medium">
                              Dealer Packaging: <strong>{prod.calculated_bottles}</strong>
                            </div>
                          )}
                          {prod.calculated_total_water && (
                            <div className="text-[10px] text-blue-700 font-medium">
                              Water: {prod.calculated_total_water}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Safety & Combination Partner */}
                      <div className="space-y-1.5 pt-1 text-xs">
                        {prod.combination_partner && (
                          <div className="p-2 rounded-lg bg-blue-50 border border-blue-200 text-[11px] text-blue-900 leading-snug">
                            <strong>Recommended Mix:</strong> {prod.combination_partner}
                          </div>
                        )}

                        {prod.bee_toxicity_warning && (
                          <div className="p-1.5 rounded-lg bg-amber-50 border border-amber-200 text-[10px] text-amber-900 font-medium flex items-center gap-1.5">
                            <span>🐝</span>
                            <span>{prod.bee_toxicity_warning}</span>
                          </div>
                        )}

                        <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                          <span>PHI: <strong>{prod.phi_days ? `${prod.phi_days} Days` : 'Label'}</strong></span>
                          <span>REI: <strong>{prod.rei_hours ? `${prod.rei_hours} Hours` : '24h'}</strong></span>
                          <span>FRAC: <strong>Registered</strong></span>
                        </div>
                      </div>
                    </div>

                    <a
                      href={prod.product_url || 'https://naclind.com/products/'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center justify-between text-xs font-bold text-[#d96b27] hover:text-[#c55d1d] pt-2.5 border-t border-[#eae4dc] transition-colors"
                    >
                      <span>View Official Product Page</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* SECTION D: Gemini AI Agronomist Synthesis */}
          <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 sm:p-7 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#eae4dc]">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-[#fdf3ed] border border-[#f5d5c0] text-[#d96b27]">
                  <Stethoscope className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-slate-900">
                    Senior Agronomist Advisory Synthesis
                  </h3>
                  <p className="text-xs text-slate-500">
                    Comprehensive treatment protocol synthesized across foliar pathology and local climatology.
                  </p>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#fdeade] text-[#d96b27] border border-[#f5d5c0] flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                <span>Gemini AI Agronomist</span>
              </span>
            </div>

            <div className="p-4 rounded-xl bg-[#fbf9f5] border border-[#eae4dc] text-xs sm:text-sm text-slate-800 leading-relaxed whitespace-pre-line space-y-2">
              {advisoryResult.ai_advisory_summary}
            </div>
          </div>

          {/* SECTION E: Cultural Remedies & Application Safety / Resistance Management */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Cultural & Agronomic Remedies */}
            <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 shadow-xs space-y-4">
              <div className="flex items-center gap-2.5 pb-2.5 border-b border-[#eae4dc]">
                <div className="p-2 rounded-lg bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0]">
                  <Sprout className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">
                    Cultural & Agronomic IPM Remedies
                  </h4>
                  <span className="text-[10px] text-slate-400">Non-chemical preventive practices</span>
                </div>
              </div>

              <div className="space-y-2.5">
                {advisoryResult.cultural_remedies.map((rem, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-[#fbf9f5] border border-[#eae4dc] text-xs text-slate-700 flex items-start gap-2.5"
                  >
                    <CheckCircle2 className="w-4 h-4 text-[#d96b27] shrink-0 mt-0.5" />
                    <span className="leading-relaxed">{rem}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Application & Resistance Management */}
            <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 shadow-xs space-y-4">
              <div className="flex items-center gap-2.5 pb-2.5 border-b border-[#eae4dc]">
                <div className="p-2 rounded-lg bg-blue-50 text-blue-600 border border-blue-200">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">
                    Application Technique & Resistance Management
                  </h4>
                  <span className="text-[10px] text-slate-400">Beneficial remedy prioritization & sprayer calibration</span>
                </div>
              </div>

              <div className="space-y-2.5">
                {advisoryResult.chemical_management.map((chem, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-[#fbf9f5] border border-[#eae4dc] text-xs text-slate-700 flex items-start gap-2.5"
                  >
                    <ShieldAlert className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                    <span className="leading-relaxed">{chem}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SECTION F: Application Safety, Personal Protective Equipment (PPE) & Disclaimer */}
          <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 shadow-xs space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-[#eae4dc]">
              <ShieldAlert className="w-4 h-4 text-[#d96b27]" />
              <h4 className="text-sm font-bold text-slate-900">
                Application Safety Protocol & Operator PPE Requirements
              </h4>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-[#fbf9f5] border border-[#eae4dc] space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Respiratory Safety</span>
                <span className="font-bold text-slate-800">Particulate Respirator</span>
                <p className="text-[10px] text-slate-500">Prevent aerosol inhalation during atomization.</p>
              </div>

              <div className="p-3 rounded-xl bg-[#fbf9f5] border border-[#eae4dc] space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Dermal Barrier</span>
                <span className="font-bold text-slate-800">Nitrile Chemical Gloves</span>
                <p className="text-[10px] text-slate-500">Wear during chemical tank mixing and pouring.</p>
              </div>

              <div className="p-3 rounded-xl bg-[#fbf9f5] border border-[#eae4dc] space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Ocular Protection</span>
                <span className="font-bold text-slate-800">Sealed Safety Goggles</span>
                <p className="text-[10px] text-slate-500">Shield eyes from pressurized splashback.</p>
              </div>

              <div className="p-3 rounded-xl bg-[#fbf9f5] border border-[#eae4dc] space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Field Re-Entry</span>
                <span className="font-bold text-slate-800">REI: 24–48 Hours</span>
                <p className="text-[10px] text-slate-500">Do not enter treated zones prior to dry-down.</p>
              </div>
            </div>

            {/* Official Statutory Disclaimer */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500 flex items-start gap-2.5">
              <HelpCircle className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
              <p className="leading-relaxed">
                {advisoryResult.safety_disclaimer}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* FULLSCREEN SPECIMEN IMAGE ZOOM MODAL */}
      {isImageModalOpen && activeSpecimenImage && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setIsImageModalOpen(false)}
        >
          <div
            className="relative max-w-4xl max-h-[90vh] bg-white rounded-2xl overflow-hidden shadow-2xl border border-slate-700 space-y-0"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="bg-slate-900 px-4 py-3 text-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sprout className="w-4 h-4 text-[#d96b27]" />
                <span className="text-xs font-bold">
                  Diagnostic Leaf Specimen — {advisoryResult?.crop_name}
                </span>
                {advisoryResult?.pest_name && (
                  <span className="text-[10px] bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded font-mono">
                    {advisoryResult.pest_name}
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={() => setIsImageModalOpen(false)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-white transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="max-h-[75vh] overflow-auto flex items-center justify-center bg-black">
              <img
                src={activeSpecimenImage}
                alt="High-resolution diagnosed leaf specimen"
                className="max-h-[75vh] w-auto object-contain"
              />
            </div>

            <div className="bg-white px-4 py-3 border-t border-[#eae4dc] flex items-center justify-between text-xs text-slate-600">
              <span>
                Preserved from Leaf Diagnosis Audit Record (ID: {advisoryResult?.advisory_id || 'Specimen'})
              </span>
              <button
                type="button"
                onClick={() => setIsImageModalOpen(false)}
                className="px-3 py-1 bg-[#d96b27] hover:bg-[#c55d1d] text-white text-xs font-bold rounded-lg transition-colors cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
