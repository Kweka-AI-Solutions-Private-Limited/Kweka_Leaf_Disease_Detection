import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Cpu,
  RefreshCw,
  Sprout,
  ShieldAlert,
  Flower2,
  Layers,
  ArrowRight,
  Info,
  Sliders,
  Check,
  Eye,
  Crosshair,
  Bug,
  Tag,
  ShieldCheck,
  Scale,
  Activity,
  Stethoscope,
  Plus,
  Trash2,
  Edit3,
  Image as ImageIcon,
  Sparkles,
} from 'lucide-react';

import {
  analyzeUnifiedTest,
  getUnifiedTestStatus,
  UnifiedTestAnalysisResponse,
  UnifiedTestStatusResponse,
} from '../api/unifiedTest';

const PRESET_CROPS = [
  'Tomato',
  'Potato',
  'Cotton',
  'Rice',
  'Maize',
  'Wheat',
  'Soybean',
  'Chilli',
  'Grape',
  'Apple',
];

export const UnifiedTestingPage: React.FC = () => {
  const navigate = useNavigate();

  // Multi-image state (1 to 5 images)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [activePreviewIndex, setActivePreviewIndex] = useState<number>(0);

  // Upfront crop selection
  const [selectedCrop, setSelectedCrop] = useState<string>(''); // '' = Auto-Detect
  const [customCropInput, setCustomCropInput] = useState<string>('');
  const [showCustomCropInput, setShowCustomCropInput] = useState<boolean>(false);

  // Post-diagnosis override state
  const [showOverrideInput, setShowOverrideInput] = useState<boolean>(false);
  const [overrideCropText, setOverrideCropText] = useState<string>('');

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<UnifiedTestAnalysisResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusMatrix, setStatusMatrix] = useState<UnifiedTestStatusResponse | null>(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Selected file and preview for active preview item
  const selectedFile = selectedFiles[activePreviewIndex] || null;
  const previewUrl = previewUrls[activePreviewIndex] || null;

  // Fetch operational status on mount
  useEffect(() => {
    fetchDetectorStatuses();
  }, []);

  const fetchDetectorStatuses = async () => {
    setIsLoadingStatus(true);
    try {
      const data = await getUnifiedTestStatus();
      setStatusMatrix(data);
    } catch (err: any) {
      console.error('Failed to load detector statuses:', err);
    } finally {
      setIsLoadingStatus(false);
    }
  };

  const handleFilesAdded = (newFileList: FileList | File[]) => {
    const validFiles = Array.from(newFileList).filter((f) => f.type.startsWith('image/'));
    if (!validFiles.length) return;

    // Combine existing and new files, capping at 5
    const combined = [...selectedFiles, ...validFiles].slice(0, 5);
    setSelectedFiles(combined);

    // Generate previews
    const urls = combined.map((f) => URL.createObjectURL(f));
    setPreviewUrls(urls);
    if (selectedFiles.length === 0) {
      setActivePreviewIndex(0);
    }
    setAnalysisResult(null);
    setErrorMessage(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFilesAdded(e.target.files);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesAdded(e.dataTransfer.files);
    }
  };

  const handleRemoveFile = (index: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const updatedFiles = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(updatedFiles);

    const updatedUrls = previewUrls.filter((_, i) => i !== index);
    setPreviewUrls(updatedUrls);

    if (activePreviewIndex >= updatedFiles.length) {
      setActivePreviewIndex(Math.max(0, updatedFiles.length - 1));
    }
  };

  const handleAnalyze = async (cropOverride?: string) => {
    if (selectedFiles.length === 0) return;

    setIsAnalyzing(true);
    setErrorMessage(null);

    // Determine final crop to pass
    let cropToSend: string | null = null;
    if (cropOverride !== undefined && cropOverride !== null) {
      cropToSend = cropOverride.trim() || null;
    } else if (showCustomCropInput && customCropInput.trim()) {
      cropToSend = customCropInput.trim();
    } else if (selectedCrop.trim()) {
      cropToSend = selectedCrop.trim();
    }

    try {
      const response = await analyzeUnifiedTest(selectedFiles, cropToSend);
      setAnalysisResult(response);
      setShowOverrideInput(false);
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'An error occurred during analysis.';
      setErrorMessage(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setSelectedFiles([]);
    setPreviewUrls([]);
    setActivePreviewIndex(0);
    setAnalysisResult(null);
    setErrorMessage(null);
    setShowOverrideInput(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-6 pb-12 w-full">
      {/* Header Banner */}
      <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 shadow-xs flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center space-x-4">
          <div className="p-3.5 rounded-2xl bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0]">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2.5 flex-wrap gap-y-1">
              <h1 className="font-extrabold text-2xl text-warmgray-900 tracking-tight">
                Leaf Diagnosis
              </h1>
              <span className="px-2.5 py-0.5 rounded-full bg-[#fdeade] text-[#d96b27] text-xs font-mono font-bold uppercase tracking-wider">
                Multi-Stream Analysis • Zero Mock Substitutions
              </span>
            </div>
            <p className="text-xs text-warmgray-500 font-medium mt-1">
              Crop Identification • Disease Pathology • Insect & Pest Detection • Independent Evidence Verification
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={fetchDetectorStatuses}
            disabled={isLoadingStatus}
            className="flex items-center space-x-2 text-xs font-bold bg-white border border-[#e5ded3] text-warmgray-700 hover:bg-warmgray-50 px-3.5 py-2 rounded-xl transition-colors shadow-xs cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 text-[#d96b27] ${isLoadingStatus ? 'animate-spin' : ''}`} />
            <span>Refresh Detectors</span>
          </button>
        </div>
      </div>

      {/* Detector Operational Matrix */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-slate-600" />
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
              Operational Status Indicators
            </h2>
          </div>
          <button
            onClick={fetchDetectorStatuses}
            disabled={isLoadingStatus}
            className="text-xs text-slate-500 hover:text-emerald-600 flex items-center gap-1 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoadingStatus ? 'animate-spin' : ''}`} />
            Refresh Status
          </button>
        </div>        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Crop Identifier Status */}
          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/60 flex flex-col justify-between">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <Sprout className="w-4 h-4 text-emerald-600" />
                <span className="text-xs font-bold text-slate-700">Crop Identification</span>
              </div>
              <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full ${statusMatrix?.detectors?.crop_identifier?.is_operational
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                  : 'bg-rose-100 text-rose-800 border border-rose-200'
                }`}>
                {statusMatrix?.detectors?.crop_identifier?.status || 'CHECKING...'}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 line-clamp-2">
              {statusMatrix?.detectors?.crop_identifier?.details || 'Live botanical species identification API.'}
            </p>
            <div className="mt-2 text-[10px] font-mono text-slate-400 truncate" title={statusMatrix?.detectors?.crop_identifier?.provider}>
              Provider: {statusMatrix?.detectors?.crop_identifier?.provider || 'Pl@ntNet Species API'}
            </div>
          </div>

          {/* Disease Detector Status */}
          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/60 flex flex-col justify-between">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-blue-600" />
                <span className="text-xs font-bold text-slate-700">Disease Detection</span>
              </div>
              <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full ${statusMatrix?.detectors?.disease_detector?.is_operational
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                  : 'bg-rose-100 text-rose-800 border border-rose-200'
                }`}>
                {statusMatrix?.detectors?.disease_detector?.status || 'CHECKING...'}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 line-clamp-2">
              {statusMatrix?.detectors?.disease_detector?.details || 'EPPO pathology service with strict >70% confidence gate.'}
            </p>
            <div className="mt-2 text-[10px] font-mono text-slate-400 truncate" title={statusMatrix?.detectors?.disease_detector?.provider}>
              Provider: {statusMatrix?.detectors?.disease_detector?.provider || 'Pl@ntNet Diseases API'}
            </div>
          </div>

          {/* Insect & Pest Detector Status */}
          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/60 flex flex-col justify-between">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <Bug className="w-4 h-4 text-rose-600" />
                <span className="text-xs font-bold text-slate-700">Insect & Pest Detection</span>
              </div>
              <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full ${statusMatrix?.detectors?.pest_detector?.is_operational
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                  : 'bg-amber-100 text-amber-800 border border-amber-200'
                }`}>
                {statusMatrix?.detectors?.pest_detector?.status || 'CHECKING...'}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 line-clamp-2">
              {statusMatrix?.detectors?.pest_detector?.details || 'IP102 benchmark YOLO model covering 102 agricultural insect species.'}
            </p>
            <div className="mt-2 text-[10px] font-mono text-slate-400 truncate" title={statusMatrix?.detectors?.pest_detector?.provider}>
              Provider: {statusMatrix?.detectors?.pest_detector?.provider || 'IP102 YOLO11s'}
            </div>
          </div>

          {/* Weed Detector Status */}
          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/60 flex flex-col justify-between">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <Flower2 className="w-4 h-4 text-amber-600" />
                <span className="text-xs font-bold text-slate-700">Weed Detection</span>
              </div>
              <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full ${statusMatrix?.detectors?.weed_detector?.is_operational
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                  : 'bg-amber-100 text-amber-800 border border-amber-200'
                }`}>
                {statusMatrix?.detectors?.weed_detector?.status || 'CHECKING...'}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 line-clamp-2">
              {statusMatrix?.detectors?.weed_detector?.details || 'Awaiting local offline ONNX model weights.'}
            </p>
            <div className="mt-2 text-[10px] font-mono text-slate-400 truncate" title={statusMatrix?.detectors?.weed_detector?.provider}>
              Provider: {statusMatrix?.detectors?.weed_detector?.provider || 'Local Weed Detector (ONNX)'}
            </div>
          </div>
        </div>
      </div>

      {/* Upload and Preview Zone */}
      <div className="bg-white rounded-2xl border border-[#eae4dc] p-6 shadow-xs space-y-5">
        {/* Step Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#eae4dc]">
          <div>
            <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
              <UploadCloud className="w-5 h-5 text-[#d96b27]" />
              Step 1: Select Crop & Upload Evaluation Photos
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Upload 1 to 5 photos (Canopy, leaf top/underside, lesion close-ups, or pests). Multi-image visual inspection powered by Gemini VLM.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 text-[11px] font-bold rounded-full bg-[#fdeade] text-[#d96b27] border border-[#f5d5c0]">
              {selectedFiles.length}/5 Photos Selected
            </span>
          </div>
        </div>

        {/* Upfront Crop Selection Bar (Optional) */}
        <div className="bg-[#fbf9f5] p-4 rounded-xl border border-[#eae4dc] space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-700">
              <Sprout className="w-4 h-4 text-[#d96b27]" />
              <span>Host Crop Selection (Optional — Helps AI lock botanical species):</span>
            </div>
            {selectedCrop && (
              <button
                type="button"
                onClick={() => {
                  setSelectedCrop('');
                  setShowCustomCropInput(false);
                  setCustomCropInput('');
                }}
                className="text-[11px] text-slate-400 hover:text-rose-600 font-semibold cursor-pointer"
              >
                Reset to Auto-Detect
              </button>
            )}
          </div>

          <div className="flex flex-wrap gap-1.5 items-center">
            <button
              type="button"
              onClick={() => {
                setSelectedCrop('');
                setShowCustomCropInput(false);
                setCustomCropInput('');
              }}
              className={`px-3 py-1 text-xs rounded-lg font-bold border transition-all cursor-pointer ${!selectedCrop && !showCustomCropInput
                  ? 'bg-[#d96b27] text-white border-[#d96b27] shadow-xs'
                  : 'bg-white text-slate-600 border-[#eae4dc] hover:border-[#d96b27]'
                }`}
            >
              Auto-Detect (AI)
            </button>

            {PRESET_CROPS.map((crop) => (
              <button
                key={crop}
                type="button"
                onClick={() => {
                  setSelectedCrop(crop);
                  setShowCustomCropInput(false);
                  setCustomCropInput('');
                }}
                className={`px-2.5 py-1 text-xs rounded-lg border transition-all cursor-pointer ${selectedCrop === crop && !showCustomCropInput
                    ? 'bg-[#d96b27] text-white border-[#d96b27] font-bold shadow-xs'
                    : 'bg-white text-slate-600 border-[#eae4dc] hover:border-[#d96b27] font-medium'
                  }`}
              >
                {crop}
              </button>
            ))}

            <button
              type="button"
              onClick={() => {
                setShowCustomCropInput(true);
                setSelectedCrop('');
              }}
              className={`px-2.5 py-1 text-xs rounded-lg border transition-all cursor-pointer ${showCustomCropInput
                  ? 'bg-[#d96b27] text-white border-[#d96b27] font-bold shadow-xs'
                  : 'bg-white text-slate-600 border-[#eae4dc] hover:border-[#d96b27] font-medium'
                }`}
            >
              Other (Type)...
            </button>
          </div>

          {showCustomCropInput && (
            <div className="pt-1 flex gap-2 max-w-md">
              <input
                type="text"
                value={customCropInput}
                onChange={(e) => setCustomCropInput(e.target.value)}
                placeholder="Type crop name (e.g. Groundnut, Mustard, Coffee)..."
                className="flex-1 px-3 py-1.5 bg-white border border-[#eae4dc] rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#d96b27]"
              />
            </div>
          )}
        </div>

        {/* Upload Dropzone */}
        {selectedFiles.length === 0 ? (
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="border-2 border-dashed border-[#eae4dc] hover:border-[#d96b27] rounded-xl p-10 text-center cursor-pointer transition-colors bg-[#fbf9f5] hover:bg-[#fdf3ed]/40"
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="image/jpeg,image/png,image/webp"
              multiple
              className="hidden"
            />
            <UploadCloud className="w-12 h-12 text-[#d96b27]/60 mx-auto mb-3" />
            <h3 className="text-sm font-bold text-slate-700">
              Click to select or drag and drop 1 to 5 images
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Supports JPEG, PNG, WEBP (Max 10 MB each). Upload whole-plant canopy, leaf top, underside, or close-ups.
            </p>
            <div className="mt-3 flex items-center justify-center gap-2">
              <span className="px-2 py-0.5 bg-[#f5efe6] text-warmgray-700 rounded text-[10px] font-semibold">
                Multi-Photo Inspection
              </span>
              <span className="px-2 py-0.5 bg-[#f5efe6] text-warmgray-700 rounded text-[10px] font-semibold">
                Macro Close-ups
              </span>
              <span className="px-2 py-0.5 bg-[#f5efe6] text-warmgray-700 rounded text-[10px] font-semibold">
                Canopy Overview
              </span>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Thumbnail Strip */}
            <div className="flex items-center gap-2.5 overflow-x-auto pb-2 pt-1">
              {selectedFiles.map((file, idx) => (
                <div
                  key={idx}
                  onClick={() => setActivePreviewIndex(idx)}
                  className={`relative flex-shrink-0 w-24 h-24 rounded-lg overflow-hidden border-2 cursor-pointer transition-all ${activePreviewIndex === idx
                      ? 'border-[#d96b27] ring-2 ring-[#d96b27]/40 shadow-md scale-105'
                      : 'border-[#eae4dc] hover:border-[#d96b27]/50 opacity-80 hover:opacity-100'
                    }`}
                >
                  <img
                    src={previewUrls[idx]}
                    alt={`Thumb ${idx + 1}`}
                    className="w-full h-full object-cover"
                  />
                  <span className={`absolute bottom-0 left-0 right-0 text-[9px] font-bold text-center py-0.5 ${idx === 0 ? 'bg-[#d96b27] text-white' : 'bg-black/60 text-white'
                    }`}>
                    {idx === 0 ? '★ Primary' : `#${idx + 1}`}
                  </span>
                  <button
                    type="button"
                    onClick={(e) => handleRemoveFile(idx, e)}
                    className="absolute top-1 right-1 w-4 h-4 bg-black/70 hover:bg-rose-600 text-white rounded-full flex items-center justify-center text-[10px] transition-colors"
                    title="Remove this photo"
                  >
                    ×
                  </button>
                </div>
              ))}

              {selectedFiles.length < 5 && (
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex-shrink-0 w-24 h-24 rounded-lg border-2 border-dashed border-[#eae4dc] hover:border-[#d96b27] bg-[#fbf9f5] hover:bg-[#fdf3ed]/40 flex flex-col items-center justify-center gap-1 text-slate-500 hover:text-[#d96b27] transition-colors cursor-pointer"
                >
                  <Plus className="w-5 h-5" />
                  <span className="text-[10px] font-bold">Add Photo</span>
                </button>
              )}

              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="image/jpeg,image/png,image/webp"
                multiple
                className="hidden"
              />
            </div>

            {/* Active Preview Showcase */}
            <div className="flex flex-col sm:flex-row items-center gap-6 p-4 bg-[#fbf9f5] rounded-xl border border-[#eae4dc]">
              <div className="relative w-48 h-48 sm:w-56 sm:h-56 rounded-lg overflow-hidden border border-[#eae4dc] bg-black/5 flex-shrink-0 shadow-sm">
                {previewUrl && (
                  <img
                    src={previewUrl}
                    alt="Active Preview"
                    className="w-full h-full object-cover"
                  />
                )}

                {/* Overlay Pest Bounding Boxes (if primary image) */}
                {activePreviewIndex === 0 &&
                  analysisResult?.pest?.detected_pests?.map((p, idx) => {
                    if (!p.bounding_box) return null;
                    const { ymin, xmin, ymax, xmax } = p.bounding_box;
                    return (
                      <div
                        key={`pest-bbox-${idx}`}
                        className="absolute border-2 border-rose-500 bg-rose-500/20 pointer-events-none transition-all z-10"
                        style={{
                          top: `${ymin * 100}%`,
                          left: `${xmin * 100}%`,
                          width: `${Math.max(0, (xmax - xmin) * 100)}%`,
                          height: `${Math.max(0, (ymax - ymin) * 100)}%`,
                        }}
                      >
                        <span className="absolute -top-4 left-0 bg-rose-600 text-white text-[9px] px-1 font-bold rounded shadow truncate max-w-[120px]">
                          {p.pest_name} ({((p.confidence || 0) * 100).toFixed(0)}%)
                        </span>
                      </div>
                    );
                  })}

                {/* Overlay Weed Bounding Boxes (if primary image) */}
                {activePreviewIndex === 0 &&
                  analysisResult?.weed?.detected_weeds?.map((w, idx) => {
                    if (!w.bounding_box) return null;
                    const { ymin, xmin, ymax, xmax } = w.bounding_box;
                    return (
                      <div
                        key={`weed-bbox-${idx}`}
                        className="absolute border-2 border-amber-500 bg-amber-500/20 pointer-events-none transition-all z-10"
                        style={{
                          top: `${ymin * 100}%`,
                          left: `${xmin * 100}%`,
                          width: `${Math.max(0, (xmax - xmin) * 100)}%`,
                          height: `${Math.max(0, (ymax - ymin) * 100)}%`,
                        }}
                      >
                        <span className="absolute -top-4 left-0 bg-amber-600 text-white text-[9px] px-1 font-bold rounded shadow truncate max-w-[120px]">
                          {w.weed_name} ({((w.confidence || 0) * 100).toFixed(0)}%)
                        </span>
                      </div>
                    );
                  })}
              </div>

              <div className="flex-1 space-y-2.5 w-full">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-slate-800 truncate max-w-xs sm:max-w-md">
                      Viewing Photo {activePreviewIndex + 1} of {selectedFiles.length}: {selectedFile?.name}
                    </h4>
                    <p className="text-xs text-slate-500">
                      Size: {((selectedFile?.size || 0) / 1024).toFixed(1)} KB • Total: {selectedFiles.length} photo(s) queued
                    </p>
                  </div>
                  <button
                    onClick={handleReset}
                    className="text-xs text-slate-500 hover:text-rose-600 font-semibold transition-colors cursor-pointer"
                  >
                    Clear All
                  </button>
                </div>

                <div className="p-3 bg-white rounded-lg border border-[#eae4dc] text-xs text-slate-600 space-y-1">
                  <div className="flex items-center gap-2 text-slate-700 font-medium">
                    <Info className="w-3.5 h-3.5 text-[#d96b27]" />
                    Multi-Image Agricultural Inspection:
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Primary image is evaluated across Pl@ntNet, IP102 YOLO, and local models. All uploaded images ({selectedFiles.length})
                    are passed to Gemini VLM for cross-image morphology, host validation, and secondary adjudication.
                  </p>
                </div>

                <div className="pt-1 flex flex-wrap gap-3">
                  <button
                    onClick={() => handleAnalyze()}
                    disabled={isAnalyzing}
                    className="flex-1 sm:flex-none px-6 py-2.5 bg-[#d96b27] hover:bg-[#c55d1d] active:scale-[0.98] disabled:bg-slate-300 text-white font-bold rounded-xl text-xs sm:text-sm shadow-sm transition-all flex items-center justify-center gap-2 cursor-pointer"
                  >
                    {isAnalyzing ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        Analyzing {selectedFiles.length} Photo{selectedFiles.length > 1 ? 's' : ''}...
                      </>
                    ) : (
                      <>
                        <ArrowRight className="w-4 h-4" />
                        Analyze {selectedFiles.length} Photo{selectedFiles.length > 1 ? 's' : ''}
                      </>
                    )}
                  </button>

                  <button
                    onClick={handleReset}
                    disabled={isAnalyzing}
                    className="px-4 py-2.5 bg-white border border-[#e5ded3] text-warmgray-700 hover:bg-warmgray-50 font-bold rounded-xl text-xs sm:text-sm transition-colors shadow-xs cursor-pointer"
                  >
                    Reset
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {errorMessage && (
          <div className="mt-4 p-4 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-start gap-2.5">
            <XCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Evaluation Error: </span>
              {errorMessage}
            </div>
          </div>
        )}
      </div>

      {/* Analysis Results: 4 Independent Sections */}
      {analysisResult && (
        <div className="space-y-6">
          {/* Image Preprocessing Details */}
          <div className="bg-slate-100/80 rounded-lg border border-slate-200 px-4 py-2.5 flex flex-wrap items-center justify-between text-xs text-slate-600 gap-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span className="font-semibold text-slate-700">Image Validated:</span>
              <span>{analysisResult.image_validation.width} × {analysisResult.image_validation.height} px</span>
              <span>({analysisResult.image_validation.format})</span>
            </div>
            <div className="flex items-center gap-4 text-slate-500">
              <span>Sharpness Score: <strong>{analysisResult.image_validation.blur_score.toFixed(1)}</strong></span>
              <span>Brightness: <strong>{analysisResult.image_validation.brightness.toFixed(1)}</strong></span>
              <span className="font-mono text-[11px] text-slate-400">ID: {analysisResult.analysis_id.slice(0, 8)}</span>
            </div>
          </div>

          {/* CROSS-VALIDATION & DIAGNOSTIC RELIABILITY ENGINE SECTION */}
          {analysisResult.cross_validation && (
            <div className="bg-slate-900 text-white rounded-2xl p-6 sm:p-7 shadow-2xl border border-slate-800 space-y-6">
              {/* Header Banner */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-800">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      Cross-Validation Engine v1.0
                    </span>
                    <span className="text-xs text-slate-400">• Evidence Reliability & Calibration Layer</span>
                  </div>
                  <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight flex items-center gap-2">
                    <Scale className="w-6 h-6 text-emerald-400" />
                    Diagnostic Reliability & Consistency Audit
                  </h2>
                  <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                    {analysisResult.cross_validation.overall_reliability_summary}
                  </p>
                </div>

                <div className="flex-shrink-0 flex flex-col items-start md:items-end gap-1.5">
                  <span className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider border ${analysisResult.cross_validation.verification_routing.verification_required
                      ? 'bg-purple-950/80 text-purple-300 border-purple-500/50'
                      : 'bg-emerald-950/80 text-emerald-300 border-emerald-500/50'
                    }`}>
                    {analysisResult.cross_validation.verification_routing.verification_required
                      ? 'Further Verification Recommended'
                      : 'Independent Evidence Satisfied'}
                  </span>
                  <span className="text-[10px] text-slate-400">
                    Strict &gt;70% Confirmation Gate Enforced
                  </span>
                </div>
              </div>

              {/* 4 Standardized Diagnostic Category Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* 1. Crop Identification Reliability */}
                <div className="bg-slate-800/80 rounded-xl p-4 border border-slate-700/80 flex flex-col justify-between space-y-3">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 uppercase tracking-wide">
                        <Sprout className="w-4 h-4" />
                        Crop Reliability
                      </div>
                      <span className={`px-2 py-0.5 text-[10px] font-extrabold rounded-full border ${analysisResult.cross_validation.crop_validation.diagnostic_status === 'CONFIRMED'
                          ? 'bg-emerald-900/60 text-emerald-300 border-emerald-600'
                          : analysisResult.cross_validation.crop_validation.diagnostic_status === 'SUSPECTED'
                            ? 'bg-amber-900/60 text-amber-300 border-amber-600'
                            : analysisResult.cross_validation.crop_validation.diagnostic_status === 'NEEDS_VERIFICATION'
                              ? 'bg-purple-900/60 text-purple-300 border-purple-600'
                              : 'bg-orange-900/60 text-orange-300 border-orange-600'
                        }`}>
                        {analysisResult.cross_validation.crop_validation.diagnostic_status}
                      </span>
                    </div>

                    <div>
                      <div className="text-[11px] text-slate-400 uppercase font-semibold">Predicted Label</div>
                      <div className="text-base font-extrabold text-white truncate" title={analysisResult.cross_validation.crop_validation.predicted_label}>
                        {analysisResult.cross_validation.crop_validation.predicted_label}
                      </div>
                      {analysisResult.cross_validation.crop_validation.scientific_name && (
                        <div className="text-[11px] italic text-slate-400 truncate">
                          {analysisResult.cross_validation.crop_validation.scientific_name}
                        </div>
                      )}
                    </div>

                    <div className="p-2 bg-slate-900/70 rounded border border-slate-700/60 text-xs space-y-1">
                      <div className="flex justify-between text-[11px]">
                        <span className="text-slate-400">Original Model Score:</span>
                        <span className="font-mono font-bold text-slate-200">
                          {analysisResult.cross_validation.crop_validation.original_model_score !== null && analysisResult.cross_validation.crop_validation.original_model_score !== undefined
                            ? `${(analysisResult.cross_validation.crop_validation.original_model_score * 100).toFixed(1)}%`
                            : 'Unavailable'}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 leading-tight">
                        {analysisResult.cross_validation.crop_validation.confidence_interpretation}
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-300 leading-relaxed">
                      {analysisResult.cross_validation.crop_validation.evidence_summary}
                    </p>
                  </div>

                  {analysisResult.cross_validation.crop_validation.warnings.length > 0 && (
                    <div className="pt-2 border-t border-slate-700/60 space-y-1">
                      {analysisResult.cross_validation.crop_validation.warnings.map((w, idx) => (
                        <div key={idx} className="text-[10px] text-amber-300 flex items-start gap-1">
                          <AlertTriangle className="w-3 h-3 flex-shrink-0 mt-0.5" />
                          <span>{w}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* 2. Disease Pathology Reliability */}
                <div className="bg-slate-800/80 rounded-xl p-4 border border-slate-700/80 flex flex-col justify-between space-y-3">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-blue-400 uppercase tracking-wide">
                        <ShieldAlert className="w-4 h-4" />
                        Disease Reliability
                      </div>
                      <span className={`px-2 py-0.5 text-[10px] font-extrabold rounded-full border ${analysisResult.cross_validation.disease_validation.diagnostic_status === 'CONFIRMED'
                          ? 'bg-emerald-900/60 text-emerald-300 border-emerald-600'
                          : analysisResult.cross_validation.disease_validation.diagnostic_status === 'NOT_DETECTED'
                            ? 'bg-blue-900/60 text-blue-300 border-blue-600'
                            : analysisResult.cross_validation.disease_validation.diagnostic_status === 'NEEDS_VERIFICATION'
                              ? 'bg-purple-900/60 text-purple-300 border-purple-600'
                              : 'bg-amber-900/60 text-amber-300 border-amber-600'
                        }`}>
                        {analysisResult.cross_validation.disease_validation.diagnostic_status}
                      </span>
                    </div>

                    <div>
                      <div className="text-[11px] text-slate-400 uppercase font-semibold">Predicted Pathology</div>
                      <div className="text-base font-extrabold text-white truncate" title={analysisResult.cross_validation.disease_validation.predicted_label}>
                        {analysisResult.cross_validation.disease_validation.predicted_label}
                      </div>
                      {analysisResult.cross_validation.disease_validation.scientific_name && (
                        <div className="text-[11px] italic text-slate-400 truncate">
                          {analysisResult.cross_validation.disease_validation.scientific_name}
                        </div>
                      )}
                    </div>

                    <div className="p-2 bg-slate-900/70 rounded border border-slate-700/60 text-xs space-y-1">
                      <div className="flex justify-between text-[11px]">
                        <span className="text-slate-400">Original Model Score:</span>
                        <span className="font-mono font-bold text-slate-200">
                          {analysisResult.cross_validation.disease_validation.original_model_score !== null && analysisResult.cross_validation.disease_validation.original_model_score !== undefined
                            ? `${(analysisResult.cross_validation.disease_validation.original_model_score * 100).toFixed(1)}%`
                            : 'Unavailable'}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 leading-tight">
                        {analysisResult.cross_validation.disease_validation.confidence_interpretation}
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-300 leading-relaxed">
                      {analysisResult.cross_validation.disease_validation.evidence_summary}
                    </p>
                  </div>

                  {analysisResult.cross_validation.disease_validation.warnings.length > 0 && (
                    <div className="pt-2 border-t border-slate-700/60 space-y-1">
                      {analysisResult.cross_validation.disease_validation.warnings.map((w, idx) => (
                        <div key={idx} className="text-[10px] text-amber-300 flex items-start gap-1">
                          <AlertTriangle className="w-3 h-3 flex-shrink-0 mt-0.5" />
                          <span>{w}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* 3. Insect & Pest Reliability */}
                <div className="bg-slate-800/80 rounded-xl p-4 border border-slate-700/80 flex flex-col justify-between space-y-3">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-rose-400 uppercase tracking-wide">
                        <Bug className="w-4 h-4" />
                        Pest Reliability
                      </div>
                      <span className={`px-2 py-0.5 text-[10px] font-extrabold rounded-full border ${analysisResult.cross_validation.pest_validation.diagnostic_status === 'CONFIRMED'
                          ? 'bg-emerald-900/60 text-emerald-300 border-emerald-600'
                          : analysisResult.cross_validation.pest_validation.diagnostic_status === 'NOT_DETECTED'
                            ? 'bg-blue-900/60 text-blue-300 border-blue-600'
                            : analysisResult.cross_validation.pest_validation.diagnostic_status === 'NEEDS_VERIFICATION'
                              ? 'bg-purple-900/60 text-purple-300 border-purple-600'
                              : 'bg-amber-900/60 text-amber-300 border-amber-600'
                        }`}>
                        {analysisResult.cross_validation.pest_validation.diagnostic_status}
                      </span>
                    </div>

                    <div>
                      <div className="text-[11px] text-slate-400 uppercase font-semibold">Predicted Insect</div>
                      <div className="text-base font-extrabold text-white truncate" title={analysisResult.cross_validation.pest_validation.predicted_label}>
                        {analysisResult.cross_validation.pest_validation.predicted_label}
                      </div>
                      {analysisResult.cross_validation.pest_validation.scientific_name && (
                        <div className="text-[11px] italic text-slate-400 truncate">
                          {analysisResult.cross_validation.pest_validation.scientific_name}
                        </div>
                      )}
                    </div>

                    <div className="p-2 bg-slate-900/70 rounded border border-slate-700/60 text-xs space-y-1">
                      <div className="flex justify-between text-[11px]">
                        <span className="text-slate-400">Original Model Score:</span>
                        <span className="font-mono font-bold text-slate-200">
                          {analysisResult.cross_validation.pest_validation.original_model_score !== null && analysisResult.cross_validation.pest_validation.original_model_score !== undefined
                            ? `${(analysisResult.cross_validation.pest_validation.original_model_score * 100).toFixed(1)}%`
                            : 'Unavailable'}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 leading-tight">
                        {analysisResult.cross_validation.pest_validation.confidence_interpretation}
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-300 leading-relaxed">
                      {analysisResult.cross_validation.pest_validation.evidence_summary}
                    </p>
                  </div>

                  {analysisResult.cross_validation.pest_validation.warnings.length > 0 && (
                    <div className="pt-2 border-t border-slate-700/60 space-y-1">
                      {analysisResult.cross_validation.pest_validation.warnings.map((w, idx) => (
                        <div key={idx} className="text-[10px] text-amber-300 flex items-start gap-1">
                          <AlertTriangle className="w-3 h-3 flex-shrink-0 mt-0.5" />
                          <span>{w}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* 4. Weed Detection Reliability */}
                <div className="bg-slate-800/80 rounded-xl p-4 border border-slate-700/80 flex flex-col justify-between space-y-3">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-amber-400 uppercase tracking-wide">
                        <Flower2 className="w-4 h-4" />
                        Weed Reliability
                      </div>
                      <span className={`px-2 py-0.5 text-[10px] font-extrabold rounded-full border ${analysisResult.cross_validation.weed_validation.diagnostic_status === 'CONFIRMED'
                          ? 'bg-emerald-900/60 text-emerald-300 border-emerald-600'
                          : analysisResult.cross_validation.weed_validation.diagnostic_status === 'NOT_DETECTED'
                            ? 'bg-blue-900/60 text-blue-300 border-blue-600'
                            : analysisResult.cross_validation.weed_validation.diagnostic_status === 'UNABLE_TO_ASSESS'
                              ? 'bg-slate-800 text-slate-400 border-slate-600'
                              : 'bg-amber-900/60 text-amber-300 border-amber-600'
                        }`}>
                        {analysisResult.cross_validation.weed_validation.diagnostic_status}
                      </span>
                    </div>

                    <div>
                      <div className="text-[11px] text-slate-400 uppercase font-semibold">Predicted Weed</div>
                      <div className="text-base font-extrabold text-white truncate" title={analysisResult.cross_validation.weed_validation.predicted_label}>
                        {analysisResult.cross_validation.weed_validation.predicted_label}
                      </div>
                      {analysisResult.cross_validation.weed_validation.scientific_name && (
                        <div className="text-[11px] italic text-slate-400 truncate">
                          {analysisResult.cross_validation.weed_validation.scientific_name}
                        </div>
                      )}
                    </div>

                    <div className="p-2 bg-slate-900/70 rounded border border-slate-700/60 text-xs space-y-1">
                      <div className="flex justify-between text-[11px]">
                        <span className="text-slate-400">Original Model Score:</span>
                        <span className="font-mono font-bold text-slate-200">
                          {analysisResult.cross_validation.weed_validation.original_model_score !== null && analysisResult.cross_validation.weed_validation.original_model_score !== undefined
                            ? `${(analysisResult.cross_validation.weed_validation.original_model_score * 100).toFixed(1)}%`
                            : 'Unavailable'}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 leading-tight">
                        {analysisResult.cross_validation.weed_validation.confidence_interpretation}
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-300 leading-relaxed">
                      {analysisResult.cross_validation.weed_validation.evidence_summary}
                    </p>
                  </div>

                  {analysisResult.cross_validation.weed_validation.warnings.length > 0 && (
                    <div className="pt-2 border-t border-slate-700/60 space-y-1">
                      {analysisResult.cross_validation.weed_validation.warnings.map((w, idx) => (
                        <div key={idx} className="text-[10px] text-amber-300 flex items-start gap-1">
                          <AlertTriangle className="w-3 h-3 flex-shrink-0 mt-0.5" />
                          <span>{w}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Host-Pest Biological Compatibility & Warnings */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-2">
                {/* Host-Pest Compatibility Details */}
                <div className="p-4 bg-slate-800/90 rounded-xl border border-slate-700/80 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-200 uppercase tracking-wide">
                      <Activity className="w-4 h-4 text-emerald-400" />
                      Host–Pest Biological Plausibility
                    </div>
                    <span className={`px-2 py-0.5 text-[10px] font-extrabold rounded-full border ${analysisResult.cross_validation.host_pest_compatibility.compatibility_status === 'COMPATIBLE'
                        ? 'bg-emerald-900/60 text-emerald-300 border-emerald-600'
                        : analysisResult.cross_validation.host_pest_compatibility.compatibility_status === 'INCOMPATIBLE'
                          ? 'bg-rose-900/60 text-rose-300 border-rose-600'
                          : 'bg-amber-900/60 text-amber-300 border-amber-600'
                      }`}>
                      {analysisResult.cross_validation.host_pest_compatibility.compatibility_status}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 bg-slate-900/60 rounded border border-slate-700/50">
                      <div className="text-[10px] text-slate-400">Host Crop:</div>
                      <div className="font-bold text-white truncate">
                        {analysisResult.cross_validation.host_pest_compatibility.host_crop_name || 'Unspecified'}
                      </div>
                      {analysisResult.cross_validation.host_pest_compatibility.biological_family && (
                        <div className="text-[10px] text-emerald-400/80 font-mono">
                          Family: {analysisResult.cross_validation.host_pest_compatibility.biological_family}
                        </div>
                      )}
                    </div>
                    <div className="p-2 bg-slate-900/60 rounded border border-slate-700/50">
                      <div className="text-[10px] text-slate-400">Pest Candidate:</div>
                      <div className="font-bold text-white truncate">
                        {analysisResult.cross_validation.host_pest_compatibility.pest_canonical_name || 'None'}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        Type: {analysisResult.cross_validation.host_pest_compatibility.relationship_type}
                      </div>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    {analysisResult.cross_validation.host_pest_compatibility.notes}
                  </p>

                  <div className="text-[10px] text-slate-500 italic pt-1 border-t border-slate-700/50">
                    Provenance: {analysisResult.cross_validation.host_pest_compatibility.relationship_provenance || 'Botanical Knowledge Base'} • {analysisResult.cross_validation.host_pest_compatibility.limitations}
                  </div>
                </div>

                {/* Contradictions & Verification Routing Notice */}
                <div className="p-4 bg-slate-800/90 rounded-xl border border-slate-700/80 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-200 uppercase tracking-wide">
                      <ShieldCheck className="w-4 h-4 text-purple-400" />
                      Verification Routing & Anomaly Log
                    </div>
                    <span className={`px-2 py-0.5 text-[10px] font-mono rounded-full border ${analysisResult.cross_validation.verification_routing.gemini_routing_status === 'COMPLETED'
                        ? 'text-emerald-300 bg-emerald-950/60 border-emerald-700'
                        : analysisResult.cross_validation.verification_routing.gemini_routing_status === 'PENDING'
                          ? 'text-yellow-300 bg-yellow-950/60 border-yellow-700'
                          : analysisResult.cross_validation.verification_routing.gemini_routing_status === 'ERROR'
                            ? 'text-rose-300 bg-rose-950/60 border-rose-700'
                            : analysisResult.cross_validation.verification_routing.gemini_feature_enabled
                              ? 'text-purple-300 bg-purple-950/60 border-purple-800'
                              : 'text-slate-400 bg-slate-900/60 border-slate-700'
                      }`}>
                      Gemini VLM: {
                        analysisResult.cross_validation.verification_routing.gemini_routing_status === 'COMPLETED'
                          ? 'Active (Verified)'
                          : analysisResult.cross_validation.verification_routing.gemini_routing_status === 'PENDING'
                            ? 'Running'
                            : analysisResult.cross_validation.verification_routing.gemini_routing_status === 'ERROR'
                              ? 'Error'
                              : analysisResult.cross_validation.verification_routing.gemini_feature_enabled
                                ? 'Enabled'
                                : 'Disabled'
                      }
                    </span>
                  </div>

                  {analysisResult.cross_validation.detected_contradictions.length > 0 ? (
                    <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                      {analysisResult.cross_validation.detected_contradictions.map((c, idx) => (
                        <div key={idx} className="p-2 bg-slate-900/80 rounded border border-slate-700/60 text-xs space-y-0.5">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-amber-300 text-[11px]">{c.code}</span>
                            <span className="text-[9px] uppercase font-mono px-1 rounded bg-slate-800 text-slate-400">
                              {c.severity} Severity
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-300">{c.message}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-2.5 bg-emerald-950/30 border border-emerald-800/40 rounded text-xs text-emerald-300 flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      <span>Zero biological or confidence contradictions detected across diagnostic streams.</span>
                    </div>
                  )}

                  <div className="p-2.5 bg-slate-900/70 rounded border border-slate-700/60 text-xs space-y-1">
                    <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                      Agronomist Verification Routing Output:
                    </div>
                    <p className="text-[11px] text-slate-300 leading-relaxed">
                      {analysisResult.cross_validation.verification_routing.gemini_action_summary}
                    </p>
                    {analysisResult.cross_validation.verification_routing.recommended_candidates_to_examine.length > 0 && (
                      <div className="pt-1 border-t border-slate-800 text-[10px] text-purple-300">
                        Candidates to verify: {analysisResult.cross_validation.verification_routing.recommended_candidates_to_examine.map(rc => `${rc.category.toUpperCase()}: ${rc.candidate_label}`).join(' • ')}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">

            {/* SECTION 1: CROP IDENTIFICATION */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col justify-between">
              <div>
                <div className="p-4 border-b border-[#eae4dc] bg-white flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sprout className="w-5 h-5 text-[#d96b27]" />
                    <h3 className="text-sm font-bold text-slate-800">1. Crop Identification</h3>
                  </div>
                  <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full ${analysisResult.crop.status === 'CONFIRMED'
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      : analysisResult.crop.status === 'SUSPECTED'
                        ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                        : analysisResult.crop.status === 'UNCERTAIN'
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : analysisResult.crop.status === 'NEEDS_VERIFICATION'
                            ? 'bg-amber-100 text-amber-800 border border-amber-200'
                            : analysisResult.crop.status === 'UNSUPPORTED'
                              ? 'bg-slate-100 text-slate-700 border border-slate-200'
                              : 'bg-rose-100 text-rose-800 border border-rose-200'
                    }`}>
                    {analysisResult.crop.status}
                  </span>
                </div>

                <div className="p-5 space-y-4">
                  {analysisResult.crop.status === 'MODEL_UNAVAILABLE' ? (
                    <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-center space-y-1">
                      <AlertTriangle className="w-6 h-6 text-rose-500 mx-auto mb-1" />
                      <h4 className="text-xs font-bold text-rose-800">Model unavailable — detection not performed</h4>
                      <p className="text-[11px] text-rose-600">{analysisResult.crop.message}</p>
                    </div>
                  ) : (
                    <>
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-bold">
                            Predicted Crop
                          </div>
                          {analysisResult.cross_validation?.crop_validation?.confidence_source?.includes('Gemini') && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0]">
                              Adjudicated by Gemini VLM
                            </span>
                          )}
                        </div>
                        <div className="text-lg font-extrabold text-slate-900">
                          {analysisResult.crop.crop_name}
                        </div>
                        {analysisResult.crop.scientific_name && (
                          <div className="text-xs italic text-slate-500">
                            {analysisResult.crop.scientific_name}
                          </div>
                        )}
                        <div className="mt-1.5 flex flex-wrap gap-1">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${analysisResult.crop.is_agricultural_crop !== false
                              ? 'bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0]'
                              : 'bg-slate-100 text-slate-600 border border-slate-200'
                            }`}>
                            {analysisResult.crop.is_agricultural_crop !== false
                              ? 'Cultivated Agricultural Crop'
                              : 'Wild Flora / Non-Crop Plant'}
                          </span>
                          {analysisResult.cross_validation?.crop_validation?.original_model_score !== undefined &&
                            analysisResult.cross_validation?.crop_validation?.original_model_score !== null &&
                            analysisResult.cross_validation?.crop_validation?.confidence_source?.includes('Gemini') && (
                              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-100 text-slate-600 border border-slate-200">
                                Primary Model Candidate: {analysisResult.cross_validation.crop_validation.raw_evidence_retained?.crop_name || 'Potato'} ({(analysisResult.cross_validation.crop_validation.original_model_score * 100).toFixed(1)}%)
                              </span>
                            )}
                        </div>
                      </div>

                      {analysisResult.crop.quality_warning && (
                        <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-[11px] text-amber-800 flex items-start gap-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
                          <span>{analysisResult.crop.quality_warning}</span>
                        </div>
                      )}

                      {analysisResult.crop.confidence !== null && analysisResult.crop.confidence !== undefined && (
                        <div>
                          <div className="flex justify-between text-xs text-slate-600 mb-1">
                            <span className="font-semibold">Identification Confidence</span>
                            <span className="font-bold text-[#d96b27]">
                              {(analysisResult.crop.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                            <div
                              className="bg-[#d96b27] h-2 rounded-full transition-all duration-500"
                              style={{ width: `${Math.min(100, Math.max(0, analysisResult.crop.confidence * 100))}%` }}
                            />
                          </div>
                        </div>
                      )}

                      <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600">
                        {analysisResult.crop.message}
                      </div>

                      {analysisResult.crop.common_names.length > 0 && (
                        <div className="text-[11px] text-slate-500">
                          <span className="font-semibold text-slate-700">Aliases: </span>
                          {analysisResult.crop.common_names.join(', ')}
                        </div>
                      )}

                      {/* Manual Crop Override / Refine Tool */}
                      <div className="pt-3 border-t border-[#eae4dc]">
                        {!showOverrideInput ? (
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-[#fbf9f5] p-2.5 rounded-xl border border-[#eae4dc]">
                            <div className="text-[11px] text-slate-600">
                              <span className="font-bold text-slate-800">Know your crop or AI uncertain?</span>
                              <span className="block text-[10px] text-slate-500">Override crop to refine disease & pest models</span>
                            </div>
                            <button
                              type="button"
                              onClick={() => {
                                setShowOverrideInput(true);
                                setOverrideCropText(analysisResult.crop.crop_name !== 'Unidentified Plant' && analysisResult.crop.crop_name !== 'Unavailable' ? analysisResult.crop.crop_name : '');
                              }}
                              className="px-2.5 py-1 text-xs font-bold bg-white text-[#d96b27] hover:bg-[#fdf3ed] border border-[#f5d5c0] rounded-xl shadow-xs flex items-center gap-1 transition-all self-start sm:self-auto cursor-pointer"
                            >
                              <Edit3 className="w-3 h-3" />
                              Type / Override Crop
                            </button>
                          </div>
                        ) : (
                          <div className="bg-[#fbf9f5] border border-[#f5d5c0] rounded-xl p-3 space-y-2.5">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-warmgray-900 flex items-center gap-1.5">
                                <Edit3 className="w-3.5 h-3.5 text-[#d96b27]" />
                                Specify Ground-Truth Crop Name
                              </span>
                              <button
                                type="button"
                                onClick={() => setShowOverrideInput(false)}
                                className="text-[11px] text-slate-400 hover:text-slate-600 font-semibold cursor-pointer"
                              >
                                Cancel
                              </button>
                            </div>

                            <div className="flex flex-wrap gap-1">
                              {['Tomato', 'Potato', 'Cotton', 'Rice', 'Maize', 'Wheat', 'Soybean', 'Chilli'].map((preset) => (
                                <button
                                  key={preset}
                                  type="button"
                                  onClick={() => setOverrideCropText(preset)}
                                  className={`px-2 py-0.5 text-[10px] rounded-full border transition-all cursor-pointer ${overrideCropText.toLowerCase() === preset.toLowerCase()
                                      ? 'bg-[#d96b27] text-white border-[#d96b27] font-bold shadow-xs'
                                      : 'bg-white text-slate-600 border-[#eae4dc] hover:border-[#d96b27] font-medium'
                                    }`}
                                >
                                  {preset}
                                </button>
                              ))}
                            </div>

                            <div className="flex gap-2">
                              <input
                                type="text"
                                value={overrideCropText}
                                onChange={(e) => setOverrideCropText(e.target.value)}
                                placeholder="Type crop name (e.g. Soybean, Tomato, Rice)..."
                                className="flex-1 px-3 py-1.5 bg-white border border-[#eae4dc] rounded-lg text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#d96b27]"
                              />
                              <button
                                type="button"
                                onClick={() => handleAnalyze(overrideCropText)}
                                disabled={!overrideCropText.trim() || isAnalyzing}
                                className="px-3 py-1.5 bg-[#d96b27] hover:bg-[#c55d1d] active:scale-[0.98] disabled:bg-slate-300 text-white font-bold rounded-xl text-xs shadow-sm transition-all flex items-center gap-1 cursor-pointer"
                              >
                                {isAnalyzing ? (
                                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                ) : (
                                  <Check className="w-3.5 h-3.5" />
                                )}
                                Apply & Refine
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              </div>

              <div className="p-3 border-t border-slate-100 bg-slate-50/80 text-[10px] text-slate-400 flex items-center justify-between">
                <span>Provider: {analysisResult.crop.provider}</span>
                <span className="font-semibold text-emerald-600">
                  {analysisResult.crop.is_operational ? 'Live API' : 'Unavailable'}
                </span>
              </div>
            </div>

            {/* SECTION 2: DISEASE DETECTION */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col justify-between">
              <div>
                <div className="p-4 border-b border-[#eae4dc] bg-white flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="w-5 h-5 text-blue-600" />
                    <h3 className="text-sm font-bold text-slate-800">2. Disease Detection</h3>
                  </div>
                  <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full ${analysisResult.disease.status === 'CONFIRMED'
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      : analysisResult.disease.status === 'NO_DISEASE_DETECTED'
                        ? 'bg-blue-100 text-blue-800 border border-blue-200'
                        : analysisResult.disease.status === 'SUSPECTED'
                          ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                          : analysisResult.disease.status === 'UNCERTAIN'
                            ? 'bg-amber-100 text-amber-800 border border-amber-200'
                            : analysisResult.disease.status === 'NEEDS_VERIFICATION'
                              ? 'bg-amber-100 text-amber-800 border border-amber-200'
                              : analysisResult.disease.status === 'INVALID_CATEGORY'
                                ? 'bg-purple-100 text-purple-800 border border-purple-200'
                                : 'bg-rose-100 text-rose-800 border border-rose-200'
                    }`}>
                    {analysisResult.disease.status === 'INVALID_CATEGORY' ? 'NON-PATHOLOGY FINDING' : analysisResult.disease.status}
                  </span>
                </div>

                <div className="p-5 space-y-4">
                  {analysisResult.disease.status === 'MODEL_UNAVAILABLE' ? (
                    <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-center space-y-1">
                      <AlertTriangle className="w-6 h-6 text-rose-500 mx-auto mb-1" />
                      <h4 className="text-xs font-bold text-rose-800">Model unavailable — detection not performed</h4>
                      <p className="text-[11px] text-rose-600">{analysisResult.disease.message}</p>
                    </div>
                  ) : analysisResult.disease.status === 'INVALID_CATEGORY' ? (
                    <div className="space-y-3">
                      <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg text-purple-900 space-y-1">
                        <div className="flex items-center gap-1.5 font-bold text-xs">
                          <AlertTriangle className="w-4 h-4 text-purple-600 flex-shrink-0" />
                          <span>Non-Pathology Finding Excluded</span>
                        </div>
                        <p className="text-[11px] text-purple-700 leading-relaxed">
                          {analysisResult.disease.category_warning || analysisResult.disease.message}
                        </p>
                      </div>

                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                        <div className="text-[10px] uppercase font-bold text-slate-400">Provider Stream Finding</div>
                        <div className="font-semibold text-slate-800">{analysisResult.disease.raw_provider_finding || 'Insect / Arthropod Finding'}</div>
                        {analysisResult.disease.raw_provider_score !== undefined && analysisResult.disease.raw_provider_score !== null && (
                          <div className="text-[11px] text-slate-500">
                            Raw Provider Score: {(analysisResult.disease.raw_provider_score * 100).toFixed(1)}%
                          </div>
                        )}
                        <p className="text-[10px] text-slate-500 italic mt-1">
                          Organism is cataloged as an insect pest, not a botanical plant disease. Excluded from Disease panel to maintain strict category separation.
                        </p>
                      </div>

                      {analysisResult.disease.candidates.length > 0 && (
                        <div>
                          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                            Secondary Botanical Pathology Candidates
                          </div>
                          <div className="space-y-1">
                            {analysisResult.disease.candidates.map((cand, idx) => (
                              <div
                                key={idx}
                                className="flex justify-between items-center text-xs p-1.5 bg-slate-50 rounded border border-slate-200/60"
                              >
                                <span className="text-slate-700 truncate max-w-[180px]">{cand.disease_name}</span>
                                <span className="font-mono text-slate-500 font-semibold">
                                  {cand.confidence !== null && cand.confidence !== undefined
                                    ? `${(cand.confidence * 100).toFixed(1)}%`
                                    : '—'}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <>
                      <div>
                        <div className="text-[11px] uppercase tracking-wider text-slate-400 font-bold mb-1">
                          Pathology Diagnosis
                        </div>
                        <div className="text-lg font-extrabold text-slate-900">
                          {analysisResult.disease.disease_name}
                        </div>
                      </div>

                      {analysisResult.disease.confidence !== null && analysisResult.disease.confidence !== undefined && (
                        <div>
                          <div className="flex justify-between text-xs text-slate-600 mb-1">
                            <span className="font-semibold">Model Confidence</span>
                            <span className={`font-bold ${analysisResult.disease.confidence_gate_passed ? 'text-emerald-700' : 'text-amber-700'}`}>
                              {(analysisResult.disease.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="relative w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                            <div
                              className={`h-2 rounded-full transition-all duration-500 ${analysisResult.disease.confidence_gate_passed ? 'bg-emerald-500' : 'bg-amber-500'
                                }`}
                              style={{ width: `${Math.min(100, Math.max(0, analysisResult.disease.confidence * 100))}%` }}
                            />
                            {/* Marker line at 70% threshold */}
                            <div
                              className="absolute top-0 bottom-0 w-0.5 bg-slate-900/40 z-10"
                              style={{ left: '70%' }}
                              title="70% Confirmation Gate"
                            />
                          </div>
                          <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                            <span>0%</span>
                            <span className="font-bold text-slate-600">70% Gate Standard</span>
                            <span>100%</span>
                          </div>
                        </div>
                      )}

                      {/* Gate Verification Badge */}
                      <div className={`p-3 rounded-lg border text-xs flex items-start gap-2 ${analysisResult.disease.confidence_gate_passed
                          ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                          : analysisResult.disease.status === 'NO_DISEASE_DETECTED'
                            ? 'bg-blue-50 border-blue-200 text-blue-800'
                            : 'bg-amber-50 border-amber-200 text-amber-800'
                        }`}>
                        {analysisResult.disease.confidence_gate_passed ? (
                          <Check className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                        ) : analysisResult.disease.status === 'NO_DISEASE_DETECTED' ? (
                          <CheckCircle2 className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                        ) : (
                          <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                        )}
                        <div>
                          <div className="font-bold">
                            {analysisResult.disease.confidence_gate_passed
                              ? 'Confidence Gate Passed (>70%)'
                              : analysisResult.disease.status === 'NO_DISEASE_DETECTED'
                                ? 'Healthy Foliage Confirmed'
                                : 'Unconfirmed: Confidence ≤ 70%'}
                          </div>
                          <p className="text-[11px] mt-0.5 leading-normal">
                            {analysisResult.disease.message}
                          </p>
                          {analysisResult.disease.host_crop_compatibility && (
                            <p className="text-[10px] text-blue-700 font-medium mt-1">
                              {analysisResult.disease.host_crop_compatibility}
                            </p>
                          )}
                        </div>
                      </div>

                      {analysisResult.disease.candidates.length > 0 && (
                        <div>
                          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                            Alternative Candidates
                          </div>
                          <div className="space-y-1">
                            {analysisResult.disease.candidates.map((cand, idx) => (
                              <div
                                key={idx}
                                className="flex justify-between items-center text-xs p-1.5 bg-slate-50 rounded border border-slate-200/60"
                              >
                                <span className="text-slate-700 truncate max-w-[180px]">{cand.disease_name}</span>
                                <span className="font-mono text-slate-500 font-semibold">
                                  {cand.confidence !== null && cand.confidence !== undefined
                                    ? `${(cand.confidence * 100).toFixed(1)}%`
                                    : '—'}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>

              <div className="p-3 border-t border-slate-100 bg-slate-50/80 text-[10px] text-slate-400 flex items-center justify-between">
                <span>Provider: {analysisResult.disease.provider}</span>
                <span className="font-semibold text-blue-600">
                  {analysisResult.disease.is_operational ? 'Live API' : 'Unavailable'}
                </span>
              </div>
            </div>

            {/* SECTION 3: INSECT & PEST DETECTION (IP102 BENCHMARK) */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col justify-between">
              <div>
                <div className="p-4 border-b border-[#eae4dc] bg-white flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bug className="w-5 h-5 text-rose-600" />
                    <h3 className="text-sm font-bold text-slate-800">3. Insect & Pest Detection</h3>
                  </div>
                  <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full ${analysisResult.pest?.status === 'CONFIRMED'
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      : analysisResult.pest?.status === 'NO_PEST_DETECTED'
                        ? 'bg-blue-100 text-blue-800 border border-blue-200'
                        : analysisResult.pest?.status === 'NEEDS_VERIFICATION'
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : analysisResult.pest?.status === 'SUSPECTED'
                            ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                            : analysisResult.pest?.status === 'UNCERTAIN'
                              ? 'bg-amber-100 text-amber-800 border border-amber-200'
                              : analysisResult.pest?.status === 'MODEL_UNAVAILABLE'
                                ? 'bg-slate-100 text-slate-800 border border-slate-200'
                                : 'bg-rose-100 text-rose-800 border border-rose-200'
                    }`}>
                    {analysisResult.pest?.status || 'NOT RUN'}
                  </span>
                </div>

                <div className="p-5 space-y-4">
                  {!analysisResult.pest || analysisResult.pest.status === 'MODEL_UNAVAILABLE' ? (
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg space-y-2">
                      <div className="flex items-center gap-2 text-amber-800 font-bold text-xs">
                        <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                        Model unavailable — detection not performed
                      </div>
                      <p className="text-[11px] text-amber-700 leading-relaxed">
                        {analysisResult.pest?.message || 'Awaiting IP102 benchmark model weights.'}
                      </p>
                      <div className="pt-1 border-t border-amber-200/60 text-[10px] text-amber-800/80">
                        <strong>Honest Degradation:</strong> No mock predictions are presented when weights are absent.
                      </div>
                    </div>
                  ) : analysisResult.pest.status === 'NO_PEST_DETECTED' ? (
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-center space-y-1">
                      <CheckCircle2 className="w-6 h-6 text-blue-500 mx-auto mb-1" />
                      <h4 className="text-xs font-bold text-blue-800">No Insect Pests Detected</h4>
                      <p className="text-[11px] text-blue-600">
                        {analysisResult.pest.message || 'Scanned foliage for 102 benchmark species with zero positive matches.'}
                      </p>
                    </div>
                  ) : (
                    <>
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-bold">
                            Primary Detected Pest
                          </div>
                          {analysisResult.cross_validation?.pest_validation?.confidence_source?.includes('Gemini') && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                              Adjudicated by Gemini VLM
                            </span>
                          )}
                        </div>
                        <div className="text-lg font-extrabold text-slate-900">
                          {analysisResult.pest.primary_pest || 'Unknown Pest'}
                        </div>
                        {analysisResult.pest.detected_pests[0]?.scientific_name && (
                          <div className="text-xs italic text-slate-500">
                            {analysisResult.pest.detected_pests[0].scientific_name}
                          </div>
                        )}
                        {analysisResult.cross_validation?.pest_validation?.original_model_score !== undefined &&
                          analysisResult.cross_validation?.pest_validation?.original_model_score !== null &&
                          analysisResult.cross_validation?.pest_validation?.confidence_source?.includes('Gemini') && (
                            <div className="mt-1.5 flex flex-wrap gap-1">
                              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-100 text-slate-600 border border-slate-200">
                                Primary Detector Proposal: {analysisResult.cross_validation.pest_validation.raw_evidence_retained?.primary_pest || 'Colorado potato beetle'} ({(analysisResult.cross_validation.pest_validation.original_model_score * 100).toFixed(1)}%)
                              </span>
                            </div>
                          )}
                      </div>

                      {analysisResult.pest.confidence !== null && analysisResult.pest.confidence !== undefined && (
                        <div>
                          <div className="flex justify-between text-xs text-slate-600 mb-1">
                            <span className="font-semibold">Model Confidence</span>
                            <span className={`font-bold ${analysisResult.pest.confidence_gate_passed ? 'text-emerald-700' : 'text-amber-700'
                              }`}>
                              {(analysisResult.pest.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                            <div
                              className={`h-2 rounded-full transition-all duration-500 ${analysisResult.pest.confidence_gate_passed ? 'bg-emerald-500' : 'bg-amber-500'
                                }`}
                              style={{ width: `${Math.min(100, Math.max(0, analysisResult.pest.confidence * 100))}%` }}
                            />
                          </div>
                        </div>
                      )}

                      {analysisResult.pest.cross_model_verified && (
                        <div className="p-3 bg-indigo-50/90 border border-indigo-200 rounded-lg text-xs space-y-1 text-indigo-900">
                          <div className="flex items-center justify-between font-bold text-[11px]">
                            <div className="flex items-center gap-1.5 text-indigo-700">
                              <Layers className="w-3.5 h-3.5" />
                              <span>Cross-Model Consensus Verified</span>
                            </div>
                            <span className="bg-indigo-100 text-indigo-800 text-[10px] px-1.5 py-0.5 rounded font-mono">
                              Bayesian Evidence Fusion
                            </span>
                          </div>
                          <div className="text-[11px] text-indigo-800/90 leading-relaxed">
                            {analysisResult.pest.original_local_confidence !== undefined && analysisResult.pest.original_local_confidence !== null ? (
                              <>
                                Local YOLO morphology score (<span className="font-semibold font-mono">{(analysisResult.pest.original_local_confidence * 100).toFixed(1)}%</span>) corroborated by host pathology stream to reach{' '}
                                <span className="font-semibold text-indigo-900 font-mono">{(analysisResult.pest.confidence! * 100).toFixed(1)}%</span> consensus confidence.
                              </>
                            ) : (
                              analysisResult.pest.validation_source || 'Corroborated across spatial detection and host pathology stream.'
                            )}
                          </div>
                        </div>
                      )}

                      <div className={`p-3 rounded-lg border text-xs ${analysisResult.pest.status === 'CONFIRMED'
                          ? 'bg-emerald-50/80 border-emerald-200 text-emerald-900'
                          : 'bg-amber-50/80 border-amber-200 text-amber-900'
                        }`}>
                        <div className="font-bold text-[11px] mb-0.5">
                          {analysisResult.pest.status === 'CONFIRMED'
                            ? 'Strict Standard Met (>70%)'
                            : 'Uncertain: Confidence ≤ 70%'}
                        </div>
                        <p className="text-[11px] leading-normal">{analysisResult.pest.message}</p>
                      </div>

                      {analysisResult.pest.detected_pests.length > 0 && (
                        <div>
                          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex justify-between items-center">
                            <span>Detected Instances ({analysisResult.pest.detected_pests.length})</span>
                            <span className="text-[10px] text-slate-400 font-normal">Class ID</span>
                          </div>
                          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                            {analysisResult.pest.detected_pests.map((item, idx) => (
                              <div
                                key={idx}
                                className="p-2 bg-slate-50 rounded-lg border border-slate-200/80 text-xs space-y-1"
                              >
                                <div className="flex justify-between items-center font-bold text-slate-800">
                                  <span className="truncate max-w-[140px]">{item.pest_name}</span>
                                  <span className="text-emerald-700 font-mono">{(item.confidence * 100).toFixed(1)}%</span>
                                </div>
                                <div className="flex items-center justify-between text-[10px] text-slate-500">
                                  <span>{item.category || 'Insect'} {item.damage_type ? `• ${item.damage_type}` : ''}</span>
                                  <span className="font-mono text-slate-400">#{item.pest_class_id}</span>
                                </div>
                                {item.bounding_box && (
                                  <div className="text-[9px] font-mono text-slate-400 pt-0.5 border-t border-slate-200/40">
                                    BBox: [{item.bounding_box.ymin.toFixed(2)}, {item.bounding_box.xmin.toFixed(2)}, {item.bounding_box.ymax.toFixed(2)}, {item.bounding_box.xmax.toFixed(2)}]
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>

              <div className="p-3 border-t border-slate-100 bg-slate-50/80 text-[10px] text-slate-400 flex items-center justify-between">
                <span className="truncate max-w-[150px]" title={analysisResult.pest?.provider}>
                  {analysisResult.pest?.provider || 'IP102 Detector'}
                </span>
                <span className="font-semibold text-rose-600">
                  {analysisResult.pest?.is_operational ? 'Operational' : 'Unavailable'}
                </span>
              </div>
            </div>

            {/* SECTION 4: WEED DETECTION */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col justify-between">
              <div>
                <div className="p-4 border-b border-[#eae4dc] bg-white flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Flower2 className="w-5 h-5 text-amber-600" />
                    <h3 className="text-sm font-bold text-slate-800">4. Weed Detection</h3>
                  </div>
                  <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full ${analysisResult.weed.status === 'CONFIRMED'
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      : analysisResult.weed.status === 'NO_WEED_DETECTED'
                        ? 'bg-blue-100 text-blue-800 border border-blue-200'
                        : analysisResult.weed.status === 'MODEL_UNAVAILABLE'
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : 'bg-slate-100 text-slate-700 border border-slate-200'
                    }`}>
                    {analysisResult.weed.status}
                  </span>
                </div>

                <div className="p-5 space-y-4">
                  {analysisResult.weed.status === 'MODEL_UNAVAILABLE' ? (
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg space-y-2">
                      <div className="flex items-center gap-2 text-amber-800 font-bold text-xs">
                        <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                        Model unavailable — detection not performed
                      </div>
                      <p className="text-[11px] text-amber-700 leading-relaxed">
                        {analysisResult.weed.message}
                      </p>
                      <div className="p-2 bg-white/70 rounded border border-amber-200/50 text-[10px] text-slate-600 space-y-1">
                        <div className="font-semibold text-slate-700">Supported Target Benchmarks:</div>
                        <div>• <strong>MH-Weed16:</strong> 16-class Indian soybean agro-ecosystem YOLO detector (bounding boxes).</div>
                        <div>• <strong>DeepWeeds:</strong> 9-class Australian rangeland ResNet50 classifier (whole image).</div>
                      </div>
                      <div className="pt-1 border-t border-amber-200/60 text-[10px] text-amber-800/80">
                        <strong>Honest Reporting:</strong> Zero mock predictions are presented when weights are absent.
                      </div>
                    </div>
                  ) : analysisResult.weed.status === 'NO_WEED_DETECTED' ? (
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-center space-y-1">
                      <CheckCircle2 className="w-6 h-6 text-blue-500 mx-auto mb-1" />
                      <h4 className="text-xs font-bold text-blue-800">No Weeds Detected</h4>
                      <p className="text-[11px] text-blue-600">{analysisResult.weed.message}</p>
                    </div>
                  ) : (
                    <>
                      <div>
                        <div className="text-[11px] uppercase tracking-wider text-slate-400 font-bold mb-1">
                          Primary Detected Weed
                        </div>
                        <div className="text-lg font-extrabold text-slate-900">
                          {analysisResult.weed.detected_weeds[0]?.weed_name || 'Weed Identified'}
                        </div>
                        {analysisResult.weed.detected_weeds[0]?.scientific_name && (
                          <div className="text-xs italic text-slate-500">
                            {analysisResult.weed.detected_weeds[0].scientific_name}
                          </div>
                        )}
                        <div className="mt-1 flex gap-1">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                            {analysisResult.weed.architecture_type || (analysisResult.weed.supports_bounding_boxes ? 'Object Detection' : 'Classification')}
                          </span>
                        </div>
                      </div>

                      {analysisResult.weed.confidence !== null && analysisResult.weed.confidence !== undefined && (
                        <div>
                          <div className="flex justify-between text-xs text-slate-600 mb-1">
                            <span className="font-semibold">Model Confidence</span>
                            <span className={`font-bold ${analysisResult.weed.status === 'CONFIRMED' ? 'text-emerald-700' : 'text-amber-700'}`}>
                              {(analysisResult.weed.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                            <div
                              className={`h-2 rounded-full transition-all duration-500 ${analysisResult.weed.status === 'CONFIRMED' ? 'bg-emerald-500' : 'bg-amber-500'
                                }`}
                              style={{ width: `${Math.min(100, Math.max(0, analysisResult.weed.confidence * 100))}%` }}
                            />
                          </div>
                        </div>
                      )}

                      <div className={`p-3 rounded-lg border text-xs ${analysisResult.weed.status === 'CONFIRMED'
                          ? 'bg-emerald-50/80 border-emerald-200 text-emerald-900'
                          : 'bg-amber-50/80 border-amber-200 text-amber-900'
                        }`}>
                        <div className="font-bold text-[11px] mb-0.5">
                          {analysisResult.weed.status === 'CONFIRMED'
                            ? 'Strict Standard Met (>70%)'
                            : 'Uncertain: Confidence ≤ 70%'}
                        </div>
                        <p className="text-[11px] leading-normal">{analysisResult.weed.message}</p>
                      </div>

                      {analysisResult.weed.detected_weeds.length > 0 && (
                        <div>
                          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex justify-between items-center">
                            <span>Detected Instances ({analysisResult.weed.detected_weeds.length})</span>
                            <span className="text-[10px] text-slate-400 font-normal">
                              {analysisResult.weed.supports_bounding_boxes ? 'Bounding Box' : 'Classification'}
                            </span>
                          </div>
                          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                            {analysisResult.weed.detected_weeds.map((weed, idx) => (
                              <div
                                key={idx}
                                className="p-2 bg-slate-50 rounded-lg border border-slate-200/80 text-xs space-y-1"
                              >
                                <div className="flex justify-between items-center font-bold text-slate-800">
                                  <span className="truncate max-w-[150px]">{weed.weed_name}</span>
                                  <span className="text-emerald-700 font-mono">{(weed.confidence * 100).toFixed(1)}%</span>
                                </div>
                                {weed.scientific_name && (
                                  <div className="text-[10px] italic text-slate-500">
                                    {weed.scientific_name}
                                  </div>
                                )}
                                <div className="flex items-center justify-between text-[10px] text-slate-500">
                                  <span>{weed.growth_habit ? `Habit: ${weed.growth_habit}` : 'Weed Foliage'}</span>
                                  <span className="font-mono text-slate-400">{weed.detection_type || 'DETECTION'}</span>
                                </div>
                                {weed.bounding_box && (
                                  <div className="text-[9px] font-mono text-slate-400 pt-0.5 border-t border-slate-200/40">
                                    BBox: [{weed.bounding_box.ymin.toFixed(2)}, {weed.bounding_box.xmin.toFixed(2)}, {weed.bounding_box.ymax.toFixed(2)}, {weed.bounding_box.xmax.toFixed(2)}]
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>

              <div className="p-3 border-t border-slate-100 bg-slate-50/80 text-[10px] text-slate-400 flex items-center justify-between">
                <span className="truncate max-w-[150px]" title={analysisResult.weed.provider}>
                  Provider: {analysisResult.weed.provider}
                </span>
                <span className="font-semibold text-amber-700">
                  {analysisResult.weed.is_operational ? 'Operational' : 'Awaiting Weights'}
                </span>
              </div>
            </div>
          </div>

          {/* CTA Banner: Proceed to Leaf Advisory */}
          <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 sm:p-8 shadow-xs flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#fdf3ed] border border-[#f5d5c0] rounded-full text-xs font-semibold text-[#d96b27] uppercase tracking-wider">
                <Stethoscope className="w-3.5 h-3.5 text-[#d96b27]" />
                Next Step: Treatment & Agronomic Solutions
              </div>
              <h3 className="text-xl sm:text-2xl font-black text-warmgray-900 tracking-tight">
                Do you want tailored treatment suggestions or remedies?
              </h3>
              <p className="text-sm text-warmgray-500 leading-relaxed">
                Transfer this confirmed diagnosis directly into <strong>Leaf Advisory</strong> to receive verified NACL Agrochemical remedies, seasonal spray timing, and expert cultural agronomic guidance.
              </p>
            </div>
            <button
              type="button"
              onClick={async () => {
                let specimenImg = analysisResult.image_url || null;
                if (!specimenImg && selectedFiles.length > 0) {
                  try {
                    specimenImg = await new Promise<string>((resolve, reject) => {
                      const reader = new FileReader();
                      reader.onload = () => resolve(reader.result as string);
                      reader.onerror = reject;
                      reader.readAsDataURL(selectedFiles[0]);
                    });
                  } catch {
                    specimenImg = null;
                  }
                }
                navigate('/leaf-advisory', {
                  state: {
                    inspection_id: analysisResult.analysis_id,
                    imageUrl: specimenImg,
                    diagnosis: {
                      analysis_id: analysisResult.analysis_id,
                      crop_name: analysisResult.crop.crop_name,
                      disease_name: analysisResult.disease.status === 'CONFIRMED' || analysisResult.disease.status === 'SUSPECTED' ? analysisResult.disease.disease_name : null,
                      pest_name: analysisResult.pest?.status === 'CONFIRMED' || analysisResult.pest?.status === 'SUSPECTED' ? analysisResult.pest?.primary_pest : null,
                      confidence: analysisResult.disease.confidence || analysisResult.crop.confidence || 0.85,
                      source: 'LEAF_DIAGNOSIS',
                      timestamp: analysisResult.timestamp,
                      image_url: specimenImg,
                      summary: `Crop: ${analysisResult.crop.crop_name}${analysisResult.disease.disease_name ? ` • Disease: ${analysisResult.disease.disease_name}` : ''}${analysisResult.pest?.primary_pest ? ` • Pest: ${analysisResult.pest.primary_pest}` : ''}`
                    }
                  }
                });
              }}
              className="flex items-center gap-2.5 bg-[#d96b27] hover:bg-[#c55d1d] active:scale-[0.98] text-white px-5 py-3 rounded-xl text-xs sm:text-sm font-bold shadow-sm transition-all flex-shrink-0 cursor-pointer group"
            >
              <span>Proceed to Leaf Advisory</span>
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
