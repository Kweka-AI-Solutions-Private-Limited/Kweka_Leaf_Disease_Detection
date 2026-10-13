import React, { useState, useEffect, useRef } from 'react';
import {
  Bug,
  Upload,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Info,
  Maximize2,
  RefreshCw,
  Search,
  Sliders,
  Sparkles,
  Layers,
  ShieldCheck,
  ChevronRight,
  Eye,
  FileText,
  X,
  ExternalLink,
  Cpu
} from 'lucide-react';
import { Card } from '../components/common/Card';
import {
  analyzePests,
  getPestModelStatus,
  getSupportedPestClasses,
  PestDetectionAnalysisResponse,
  PestModelStatusResponse,
  DetectedPestItem,
  PestBoundingBox,
} from '../api/pestDetection';

const POPULAR_CROPS = [
  'Rice / Paddy',
  'Corn (Maize)',
  'Cotton',
  'Tomato',
  'Wheat',
  'Citrus / Lemon',
  'Potato',
  'Brinjal / Eggplant',
  'Sugarcane',
  'Mango',
  'Soybean',
  'Pigeon Pea / Arhar',
];

export const PestDetectionPage: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [selectedPreviewIndex, setSelectedPreviewIndex] = useState<number>(0);
  const [selectedCrop, setSelectedCrop] = useState<string>('');
  const [customCropInput, setCustomCropInput] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<PestDetectionAnalysisResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [modelStatus, setModelStatus] = useState<PestModelStatusResponse | null>(null);
  const [showClassesModal, setShowClassesModal] = useState<boolean>(false);
  const [catalogClasses, setCatalogClasses] = useState<any[]>([]);
  const [classesSearch, setClassesSearch] = useState<string>('');
  const [isDragOver, setIsDragOver] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch model readiness on mount
  useEffect(() => {
    fetchModelStatus();
  }, []);

  const fetchModelStatus = async () => {
    try {
      const res = await getPestModelStatus();
      setModelStatus(res);
    } catch (e) {
      console.warn('Failed to fetch pest model status:', e);
    }
  };

  const handleOpenClassesModal = async () => {
    setShowClassesModal(true);
    if (catalogClasses.length === 0) {
      try {
        const res = await getSupportedPestClasses();
        setCatalogClasses(res.classes);
      } catch (e) {
        console.warn('Failed to load supported pest classes:', e);
      }
    }
  };

  const handleFilesSelected = (newFiles: FileList | null) => {
    if (!newFiles || newFiles.length === 0) return;
    setErrorMsg(null);

    const validNewFiles: File[] = [];
    const validPreviews: string[] = [];

    const totalAllowed = 5 - files.length;
    const limit = Math.min(newFiles.length, Math.max(0, totalAllowed));

    for (let i = 0; i < limit; i++) {
      const file = newFiles[i];
      if (file.type.startsWith('image/')) {
        validNewFiles.push(file);
        validPreviews.push(URL.createObjectURL(file));
      }
    }

    if (validNewFiles.length === 0 && newFiles.length > 0) {
      setErrorMsg('Only image files (JPEG, PNG, WEBP) are supported.');
      return;
    }

    setFiles((prev) => [...prev, ...validNewFiles]);
    setPreviews((prev) => [...prev, ...validPreviews]);
    setSelectedPreviewIndex(0);
  };

  const removeFile = (idx: number) => {
    URL.revokeObjectURL(previews[idx]);
    setFiles((prev) => prev.filter((_, i) => i !== idx));
    setPreviews((prev) => prev.filter((_, i) => i !== idx));
    if (selectedPreviewIndex >= previews.length - 1) {
      setSelectedPreviewIndex(Math.max(0, previews.length - 2));
    }
  };

  const clearAllFiles = () => {
    previews.forEach((p) => URL.revokeObjectURL(p));
    setFiles([]);
    setPreviews([]);
    setSelectedPreviewIndex(0);
    setAnalysisResult(null);
    setErrorMsg(null);
  };

  const handleStartAnalysis = async () => {
    if (files.length === 0) {
      setErrorMsg('Please upload at least 1 image containing an insect or feeding damage.');
      return;
    }

    const cropToSend = customCropInput.trim() || selectedCrop;

    setIsAnalyzing(true);
    setErrorMsg(null);
    try {
      const response = await analyzePests(files, cropToSend || undefined);
      setAnalysisResult(response);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setErrorMsg(detail);
      } else if (detail && detail.message) {
        setErrorMsg(detail.message);
      } else {
        setErrorMsg('Pest analysis encountered a server error. Please try again.');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const filteredCatalog = catalogClasses.filter(
    (c) =>
      c.name.toLowerCase().includes(classesSearch.toLowerCase()) ||
      (c.scientific_name && c.scientific_name.toLowerCase().includes(classesSearch.toLowerCase())) ||
      (c.crops && c.crops.some((crop: string) => crop.toLowerCase().includes(classesSearch.toLowerCase())))
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* ─── Header Section ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#e8dfd1]">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#1b5e20] to-[#2e7d32] flex items-center justify-center text-white shadow-sm">
              <Bug className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl font-black text-warmgray-900 tracking-tight">
              Insect & Pest Detection
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold font-mono bg-emerald-100 text-emerald-800 border border-emerald-300">
              PHASE 2
            </span>
          </div>
          <p className="text-xs text-warmgray-600 max-w-2xl">
            Agricultural entomology diagnosis powered by local IP102 deep insect taxonomy.
            Identifies 102 recognized pests, distinguishes direct insect specimens from foliage damage,
            and enforces a strict &gt;70% confidence threshold gate.
          </p>
        </div>

        {/* Model Readiness Indicator */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleOpenClassesModal}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white border border-[#e5ded3] text-xs font-bold text-warmgray-700 hover:bg-warmgray-50 transition-colors shadow-xs"
          >
            <Layers className="w-3.5 h-3.5 text-emerald-700" />
            <span>IP102 Classes (102)</span>
          </button>

          <div
            className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-mono font-bold border shadow-xs ${
              modelStatus?.status === 'online'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                : 'bg-amber-50 text-amber-900 border-amber-300'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>
              {modelStatus?.status === 'online'
                ? 'Model: Operational'
                : 'Model: Awaiting Weights'}
            </span>
          </div>
        </div>
      </div>

      {/* Model Offline / Awaiting Weights Notice */}
      {modelStatus && modelStatus.status !== 'online' && (
        <div className="p-4 rounded-2xl bg-amber-50/80 border border-amber-200/80 text-amber-950 flex items-start gap-3 shadow-xs">
          <Info className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <div className="font-bold text-amber-900">
              Local Model Architecture Configured (Awaiting Weights Checkpoint)
            </div>
            <p className="text-amber-800 leading-relaxed">
              The modular IP102 detector pipeline is active and ready. Pretrained ONNX/PyTorch checkpoint weights
              can be placed at{' '}
              <code className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 font-mono text-[11px]">
                {modelStatus.model_info.checkpoint_path || 'models/pest/ip102_detector.onnx'}
              </code>
              . When weights are absent, the system responds honestly with status{' '}
              <span className="font-mono font-bold">MODEL_UNAVAILABLE</span> and never hallucinates fake detections.
            </p>
          </div>
        </div>
      )}

      {/* ─── Main Two-Column Layout ────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Image Upload & Crop Configuration (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <Card className="p-5 space-y-5 bg-white border border-[#e8dfd1] rounded-2xl shadow-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold text-warmgray-900">
                <Upload className="w-4 h-4 text-emerald-700" />
                <span>Upload Insect or Damaged Foliage</span>
              </div>
              {files.length > 0 && (
                <button
                  type="button"
                  onClick={clearAllFiles}
                  className="text-xs font-semibold text-rose-600 hover:text-rose-800"
                >
                  Clear all
                </button>
              )}
            </div>

            {/* Drag & Drop Upload Zone */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragOver(false);
                handleFilesSelected(e.dataTransfer.files);
              }}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
                isDragOver
                  ? 'border-emerald-600 bg-emerald-50/50'
                  : 'border-[#dfd7ca] hover:border-emerald-600 hover:bg-[#faf7f2]'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={(e) => handleFilesSelected(e.target.files)}
              />
              <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
                <Bug className="w-6 h-6" />
              </div>
              <div className="text-xs font-bold text-warmgray-900 mb-1">
                Drop pest photos here, or <span className="text-emerald-700 underline">browse</span>
              </div>
              <div className="text-[11px] text-warmgray-500">
                Supports up to 5 images • JPEG, PNG, WEBP • Max 10MB each
              </div>
            </div>

            {/* Thumbnails Row */}
            {previews.length > 0 && (
              <div className="space-y-2">
                <div className="text-[11px] font-bold text-warmgray-600 uppercase font-mono">
                  Selected Images ({previews.length}/5)
                </div>
                <div className="flex items-center gap-2 overflow-x-auto pb-2">
                  {previews.map((src, i) => (
                    <div
                      key={i}
                      className={`relative w-16 h-16 rounded-xl overflow-hidden shrink-0 border-2 transition-all cursor-pointer ${
                        selectedPreviewIndex === i
                          ? 'border-emerald-600 ring-2 ring-emerald-600/30'
                          : 'border-[#e8dfd1] opacity-75 hover:opacity-100'
                      }`}
                      onClick={() => setSelectedPreviewIndex(i)}
                    >
                      <img src={src} alt="Preview" className="w-full h-full object-cover" />
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeFile(i);
                        }}
                        className="absolute top-1 right-1 w-4 h-4 bg-black/60 hover:bg-rose-600 rounded-full text-white flex items-center justify-center text-[10px]"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Optional Crop Selection */}
            <div className="space-y-2.5 pt-2 border-t border-[#f0eae1]">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-warmgray-800">
                  Target Host Crop <span className="text-warmgray-400 font-normal">(Optional)</span>
                </label>
                <span className="text-[10px] text-warmgray-500 font-mono">Improves Compatibility Check</span>
              </div>

              <div className="grid grid-cols-2 gap-1.5">
                {POPULAR_CROPS.slice(0, 8).map((crop) => (
                  <button
                    key={crop}
                    type="button"
                    onClick={() => {
                      setSelectedCrop(selectedCrop === crop ? '' : crop);
                      setCustomCropInput('');
                    }}
                    className={`px-2.5 py-1.5 rounded-lg text-xs font-medium text-left truncate transition-all ${
                      selectedCrop === crop
                        ? 'bg-emerald-100/90 text-emerald-900 border border-emerald-300 font-bold'
                        : 'bg-[#faf7f2] text-warmgray-700 hover:bg-[#ede5d8] border border-transparent'
                    }`}
                  >
                    {crop}
                  </button>
                ))}
              </div>

              <input
                type="text"
                placeholder="Or type another crop (e.g. Mustard, Coffee, Chilli)..."
                value={customCropInput}
                onChange={(e) => {
                  setCustomCropInput(e.target.value);
                  setSelectedCrop('');
                }}
                className="w-full bg-[#faf7f2] border border-[#e5ded3] rounded-xl px-3 py-2 text-xs text-warmgray-800 placeholder:text-warmgray-400 focus:outline-none focus:border-emerald-600"
              />
            </div>

            {/* Error Message */}
            {errorMsg && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Analyze Button */}
            <button
              type="button"
              disabled={files.length === 0 || isAnalyzing}
              onClick={handleStartAnalysis}
              className={`w-full py-3 rounded-xl font-bold text-xs flex items-center justify-center gap-2 text-white shadow-sm transition-all ${
                files.length === 0 || isAnalyzing
                  ? 'bg-warmgray-300 cursor-not-allowed text-warmgray-500'
                  : 'bg-emerald-700 hover:bg-emerald-800 active:scale-[0.99]'
              }`}
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  <span>Executing IP102 Entomology Analysis...</span>
                </>
              ) : (
                <>
                  <Bug className="w-4 h-4 text-white" />
                  <span>Run Pest & Entomology Inspection</span>
                </>
              )}
            </button>
          </Card>
        </div>

        {/* Right Column: Diagnostic Results & Findings (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {!analysisResult && !isAnalyzing && (
            <Card className="p-12 text-center bg-white border border-[#e8dfd1] rounded-2xl space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-800 mx-auto flex items-center justify-center">
                <Bug className="w-8 h-8 text-emerald-700" />
              </div>
              <div className="max-w-md mx-auto space-y-1">
                <h3 className="text-base font-extrabold text-warmgray-900">
                  Ready for Pest & Damage Analysis
                </h3>
                <p className="text-xs text-warmgray-500 leading-relaxed">
                  Upload an image of a plant leaf, shoot, or fruit exhibiting an insect specimen,
                  larva, or feeding damage (shot holes, mining trails, or skeletonization).
                </p>
              </div>
              <div className="pt-4 flex flex-wrap items-center justify-center gap-2 text-[11px] font-mono text-warmgray-500">
                <span className="px-2 py-1 bg-[#faf7f2] rounded border border-[#e8dfd1]">
                  Strict &gt;70% Gate
                </span>
                <span className="px-2 py-1 bg-[#faf7f2] rounded border border-[#e8dfd1]">
                  IP102 Benchmark
                </span>
                <span className="px-2 py-1 bg-[#faf7f2] rounded border border-[#e8dfd1]">
                  Specimen vs Damage Distinction
                </span>
              </div>
            </Card>
          )}

          {isAnalyzing && (
            <Card className="p-12 text-center bg-white border border-[#e8dfd1] rounded-2xl space-y-4 animate-pulse">
              <div className="w-16 h-16 rounded-2xl bg-emerald-100 text-emerald-700 mx-auto flex items-center justify-center animate-spin">
                <RefreshCw className="w-8 h-8" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-warmgray-900">
                  Validating Quality & Scanning IP102 Classes...
                </h3>
                <p className="text-xs text-warmgray-500">
                  Running Laplacian blur checks, resolution verification, and model inference.
                </p>
              </div>
            </Card>
          )}

          {analysisResult && (
            <div className="space-y-6 animate-in fade-in duration-300">
              {/* Primary Status Banner */}
              <Card
                className={`p-5 rounded-2xl border shadow-xs ${
                  analysisResult.status === 'SUCCESS'
                    ? 'bg-emerald-50/70 border-emerald-300'
                    : analysisResult.status === 'MODEL_UNAVAILABLE'
                    ? 'bg-slate-50 border-slate-300'
                    : analysisResult.status === 'NO_PEST_DETECTED'
                    ? 'bg-blue-50/70 border-blue-200'
                    : 'bg-amber-50/70 border-amber-300'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    {analysisResult.status === 'SUCCESS' ? (
                      <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0" />
                    ) : analysisResult.status === 'MODEL_UNAVAILABLE' ? (
                      <Cpu className="w-6 h-6 text-slate-600 shrink-0" />
                    ) : (
                      <AlertTriangle className="w-6 h-6 text-amber-600 shrink-0" />
                    )}
                    <div>
                      <div className="text-xs font-mono font-bold uppercase tracking-wider text-warmgray-500">
                        DIAGNOSIS STATUS
                      </div>
                      <div className="text-lg font-black text-warmgray-900">
                        {analysisResult.validation_result.diagnosis_status}
                      </div>
                    </div>
                  </div>

                  {/* Strict 70% Gate Badge */}
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-3 py-1.5 rounded-xl text-xs font-extrabold font-mono border ${
                        analysisResult.validation_result.confidence_gate_passed
                          ? 'bg-emerald-100 text-emerald-900 border-emerald-300'
                          : 'bg-amber-100 text-amber-900 border-amber-300'
                      }`}
                    >
                      {analysisResult.validation_result.confidence_gate_passed
                        ? 'CONFIRMED (>70% CONFIDENCE)'
                        : 'UNCERTAIN (GATE <=70% OR UNVERIFIED)'}
                    </span>
                  </div>
                </div>

                {/* Retry Guidance Warning if Uncertain */}
                {analysisResult.validation_result.retry_guidance && (
                  <div className="mt-4 p-3 rounded-xl bg-white/80 border border-amber-200/80 text-xs text-amber-950 flex items-start gap-2.5">
                    <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div className="leading-relaxed">
                      <span className="font-bold">Agronomist Recommendation: </span>
                      {analysisResult.validation_result.retry_guidance}
                    </div>
                  </div>
                )}
              </Card>

              {/* Primary Candidate Card */}
              {analysisResult.primary_pest ? (
                <Card className="p-5 bg-white border border-[#e8dfd1] rounded-2xl space-y-4 shadow-xs">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-100 text-emerald-800">
                          {analysisResult.primary_pest.category}
                        </span>
                        {analysisResult.validation_result.crop_host_compatibility && (
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                              analysisResult.validation_result.crop_host_compatibility === 'COMPATIBLE'
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : analysisResult.validation_result.crop_host_compatibility === 'HOST_NOT_SPECIFIED' ||
                                  analysisResult.validation_result.crop_host_compatibility === 'UNKNOWN_CROP' ||
                                  analysisResult.validation_result.crop_host_compatibility === 'UNRESTRICTED'
                                ? 'bg-slate-100 text-slate-700 border border-slate-200'
                                : 'bg-amber-50 text-amber-700 border border-amber-200'
                            }`}
                            title={
                              analysisResult.validation_result.crop_host_compatibility === 'HOST_NOT_SPECIFIED' ||
                              analysisResult.validation_result.crop_host_compatibility === 'UNKNOWN_CROP'
                                ? 'Target host crop was not selected; evaluated under general agricultural hosts'
                                : undefined
                            }
                          >
                            {analysisResult.validation_result.crop_host_compatibility === 'HOST_NOT_SPECIFIED' ||
                            analysisResult.validation_result.crop_host_compatibility === 'UNKNOWN_CROP'
                              ? 'HOST CROP: NOT SPECIFIED'
                              : analysisResult.validation_result.crop_host_compatibility}
                          </span>
                        )}
                      </div>
                      <div className="flex flex-wrap items-baseline gap-2">
                        <h2 className="text-xl font-extrabold text-warmgray-900">
                          {analysisResult.primary_pest.pest_name}
                        </h2>
                        {!analysisResult.validation_result.confidence_gate_passed && (
                          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300">
                            Provisional Candidate (Unverified)
                          </span>
                        )}
                      </div>
                      {analysisResult.primary_pest.scientific_name && (
                        <div className="text-xs text-warmgray-500 italic">
                          {analysisResult.primary_pest.scientific_name}
                        </div>
                      )}
                    </div>

                    {/* Confidence Breakdown */}
                    <div className="text-right">
                      <div className="text-2xl font-black text-emerald-700 font-mono">
                        {(analysisResult.validation_result.calibrated_confidence * 100).toFixed(1)}%
                      </div>
                      <div className="text-[10px] text-warmgray-400 font-mono">
                        Raw: {(analysisResult.primary_pest.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  {/* Biological Profile & Damage Type */}
                  <div className="p-3.5 rounded-xl bg-[#faf7f2] border border-[#ede5d8] space-y-2 text-xs">
                    {analysisResult.primary_pest.damage_type && (
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-warmgray-700">Feeding Mechanism:</span>
                          <span className="font-mono text-warmgray-900 px-2 py-0.5 rounded bg-white border border-[#e5ded3]">
                            {analysisResult.primary_pest.damage_type}
                            {!analysisResult.validation_result.confidence_gate_passed && ' (Provisional)'}
                          </span>
                        </div>
                        {!analysisResult.validation_result.confidence_gate_passed && (
                          <p className="text-[10px] text-warmgray-500 italic">
                            *Associated biological trait of catalog candidate. Visible foliar damage cannot be conclusively attributed to this insect without confirmed species identification.
                          </p>
                        )}
                      </div>
                    )}
                    {analysisResult.primary_pest.description && (
                      <p className="text-warmgray-700 leading-relaxed">
                        {analysisResult.primary_pest.description}
                      </p>
                    )}
                  </div>

                  {/* Bounding Box Information & Visual Overlay */}
                  {analysisResult.primary_pest.bounding_box && (
                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-3">
                      <div className="flex items-center justify-between font-bold text-slate-900">
                        <div className="flex items-center gap-1.5">
                          <Eye className="w-4 h-4 text-emerald-700" />
                          <span>Spatial Localization Verification</span>
                        </div>
                        <span className="text-[10px] font-mono text-slate-500 font-normal">
                          ymin: {analysisResult.primary_pest.bounding_box.ymin.toFixed(3)}, xmin: {analysisResult.primary_pest.bounding_box.xmin.toFixed(3)}, ymax: {analysisResult.primary_pest.bounding_box.ymax.toFixed(3)}, xmax: {analysisResult.primary_pest.bounding_box.xmax.toFixed(3)}
                        </span>
                      </div>

                      {/* Visual Image with Overlaid Bounding Box */}
                      {previews[selectedPreviewIndex] && (
                        <div className="relative mx-auto max-w-sm rounded-lg overflow-hidden border border-slate-300 shadow-xs bg-black/5 select-none">
                          <img
                            src={previews[selectedPreviewIndex]}
                            alt="Localized Pest"
                            className="w-full h-auto object-contain block"
                          />
                          {/* Absolute Bounding Box Overlay */}
                          <div
                            className="absolute border-2 border-emerald-500 bg-emerald-500/20 pointer-events-none transition-all"
                            style={{
                              top: `${analysisResult.primary_pest.bounding_box.ymin * 100}%`,
                              left: `${analysisResult.primary_pest.bounding_box.xmin * 100}%`,
                              height: `${(analysisResult.primary_pest.bounding_box.ymax - analysisResult.primary_pest.bounding_box.ymin) * 100}%`,
                              width: `${(analysisResult.primary_pest.bounding_box.xmax - analysisResult.primary_pest.bounding_box.xmin) * 100}%`,
                            }}
                          >
                            <span className="absolute -top-5 left-0 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-700 text-white shadow-xs whitespace-nowrap">
                              {analysisResult.primary_pest.pest_name} ({(analysisResult.primary_pest.confidence * 100).toFixed(0)}%)
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </Card>
              ) : (
                analysisResult.status !== 'MODEL_UNAVAILABLE' && (
                  <Card className="p-6 bg-white border border-[#e8dfd1] rounded-2xl text-center text-xs text-warmgray-600">
                    No insect pests localized in the submitted image.
                  </Card>
                )
              )}

              {/* Multi-Pest List (if multiple instances detected) */}
              {analysisResult.detected_pests && analysisResult.detected_pests.length > 1 && (
                <Card className="p-5 bg-white border border-[#e8dfd1] rounded-2xl space-y-3">
                  <div className="text-xs font-bold text-warmgray-800 flex items-center gap-2">
                    <Layers className="w-4 h-4 text-emerald-700" />
                    <span>Additional Detections ({analysisResult.detected_pests.length})</span>
                  </div>
                  <div className="space-y-2">
                    {analysisResult.detected_pests.map((pest, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-xl bg-[#faf7f2] border border-[#ede5d8] flex items-center justify-between text-xs"
                      >
                        <div>
                          <span className="font-bold text-warmgray-900">{pest.pest_name}</span>
                          {pest.scientific_name && (
                            <span className="text-warmgray-500 italic ml-1">
                              ({pest.scientific_name})
                            </span>
                          )}
                          <span className="ml-2 text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800">
                            {pest.category}
                          </span>
                        </div>
                        <div className="font-mono font-bold text-emerald-700">
                          {(pest.confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Image Quality & Evidence Audit Trail */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Image Quality Metrics */}
                <Card className="p-4 bg-white border border-[#e8dfd1] rounded-2xl space-y-2.5 text-xs">
                  <div className="font-bold text-warmgray-800 flex items-center gap-1.5">
                    <Sliders className="w-3.5 h-3.5 text-emerald-700" />
                    <span>Image Quality Metrics</span>
                  </div>
                  {analysisResult.validation.details[0] && (
                    <div className="space-y-1.5 text-[11px] font-mono text-warmgray-600">
                      <div className="flex justify-between">
                        <span>Resolution:</span>
                        <span className="text-warmgray-900 font-bold">
                          {analysisResult.validation.details[0].width} ×{' '}
                          {analysisResult.validation.details[0].height} px
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Sharpness (Variance):</span>
                        <span className="text-warmgray-900 font-bold">
                          {analysisResult.validation.details[0].blur_score.toFixed(1)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Brightness Index:</span>
                        <span className="text-warmgray-900 font-bold">
                          {analysisResult.validation.details[0].brightness.toFixed(1)} / 255
                        </span>
                      </div>
                    </div>
                  )}
                </Card>

                {/* Model Metadata */}
                <Card className="p-4 bg-white border border-[#e8dfd1] rounded-2xl space-y-2 text-xs">
                  <div className="font-bold text-warmgray-800 flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-emerald-700" />
                    <span>Inference Engine Info</span>
                  </div>
                  <div className="space-y-1 text-[11px] font-mono text-warmgray-600">
                    <div className="truncate">
                      <span className="text-warmgray-400">Arch: </span>
                      <span className="text-warmgray-900">{analysisResult.model_info.architecture}</span>
                    </div>
                    <div>
                      <span className="text-warmgray-400">Classes: </span>
                      <span className="text-warmgray-900">
                        {analysisResult.model_info.supported_classes_count} Classes (IP102)
                      </span>
                    </div>
                    <div className="truncate">
                      <span className="text-warmgray-400">License: </span>
                      <span className="text-warmgray-900">{analysisResult.model_info.license}</span>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Diagnostic Notes Trail */}
              {analysisResult.validation_result.validation_notes.length > 0 && (
                <Card className="p-4 bg-white border border-[#e8dfd1] rounded-2xl space-y-2 text-xs">
                  <div className="font-bold text-warmgray-800 flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-emerald-700" />
                    <span>Diagnostic Audit Trail &amp; Reasoning</span>
                  </div>
                  <ul className="space-y-1 text-warmgray-600 list-disc list-inside text-[11px]">
                    {analysisResult.validation_result.validation_notes.map((note, idx) => (
                      <li key={idx}>{note}</li>
                    ))}
                  </ul>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ─── IP102 Classes Catalog Modal ─────────────────────────────────────────── */}
      {showClassesModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-[#e8dfd1] rounded-3xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl animate-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-5 border-b border-[#e8dfd1] flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center">
                  <Layers className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-extrabold text-warmgray-900">
                    IP102 Benchmark Insect &amp; Pest Taxonomy
                  </h3>
                  <p className="text-[11px] text-warmgray-500">
                    102 agricultural insect species &amp; feeding damage guilds
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowClassesModal(false)}
                className="p-1.5 rounded-lg text-warmgray-400 hover:text-warmgray-700 hover:bg-warmgray-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Search Input */}
            <div className="p-3 border-b border-[#f0eae1] bg-[#faf7f2]">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-warmgray-400" />
                <input
                  type="text"
                  placeholder="Filter by pest name, scientific binomial, or host crop..."
                  value={classesSearch}
                  onChange={(e) => setClassesSearch(e.target.value)}
                  className="w-full bg-white border border-[#e5ded3] rounded-xl pl-8 pr-3 py-1.5 text-xs text-warmgray-800 placeholder:text-warmgray-400 focus:outline-none focus:border-emerald-600"
                />
              </div>
            </div>

            {/* List Body */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {filteredCatalog.length === 0 ? (
                <div className="text-center py-8 text-xs text-warmgray-400">
                  No classes match your filter query.
                </div>
              ) : (
                filteredCatalog.map((cls) => (
                  <div
                    key={cls.id}
                    className="p-3 rounded-xl bg-[#faf7f2] border border-[#ede5d8] text-xs space-y-1 hover:bg-[#f4efe6] transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-bold text-warmgray-900 flex items-center gap-2">
                        <span className="font-mono text-[10px] text-warmgray-400">#{cls.id}</span>
                        <span>{cls.name}</span>
                        {cls.scientific_name && (
                          <span className="text-warmgray-500 italic text-[11px]">
                            ({cls.scientific_name})
                          </span>
                        )}
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-100 text-emerald-800">
                        {cls.category}
                      </span>
                    </div>

                    <div className="text-[11px] text-warmgray-600 flex flex-wrap gap-1 items-center">
                      <span className="font-bold">Crops:</span>
                      {cls.crops?.map((crop: string, idx: number) => (
                        <span key={idx} className="px-1.5 py-0.2 bg-white rounded border border-[#e8dfd1] text-[10px]">
                          {crop}
                        </span>
                      ))}
                    </div>

                    {cls.description && (
                      <p className="text-[11px] text-warmgray-500 pt-1 leading-relaxed">
                        {cls.description}
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default PestDetectionPage;
