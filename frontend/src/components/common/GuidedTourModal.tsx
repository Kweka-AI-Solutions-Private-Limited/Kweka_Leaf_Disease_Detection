import React, { useState } from 'react';
import {
  X,
  ChevronLeft,
  ChevronRight,
  Upload,
  Sprout,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  FlaskConical,
  BarChart3,
  History,
  Layers,
  ArrowRight,
  Play,
  Check,
  Zap,
  Info,
  Sliders,
  Eye,
  BookOpen
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface GuidedTourModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const GuidedTourModal: React.FC<GuidedTourModalProps> = ({ isOpen, onClose }) => {
  const [activeStep, setActiveStep] = useState<number>(0);
  const [fieldAcres, setFieldAcres] = useState<number>(2);
  const [lesionSlider, setLesionSlider] = useState<number>(35);
  const [zoomImage, setZoomImage] = useState<string | null>(null);
  const navigate = useNavigate();

  if (!isOpen) return null;

  const tourSteps = [
    {
      id: 'upload',
      title: '1. Upload Leaf Images & Quality Check',
      badge: 'Step 1 of 5',
      tag: 'OpenCV Quality Preprocessing',
      tagColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      image: '/tour/step1_upload.png',
      description:
        'Upload 1 to 5 leaf photos (JPEG, PNG, WEBP up to 10MB each). Local OpenCV & PIL algorithms analyze image resolution, focus variance, and brightness to ensure high diagnostic accuracy.',
      highlights: [
        'Drag-and-drop & multi-file batch upload (up to 5 images per scan).',
        'OpenCV Laplacian variance calculation to flag blurry or out-of-focus images.',
        'Exposure & brightness validation to warn if images are under/over-exposed.'
      ],
      interactiveType: 'qualityCheck'
    },
    {
      id: 'species',
      title: '2. AI Plant & Crop Identification',
      badge: 'Step 2 of 5',
      tag: 'Pl@ntNet + Gemini Vision',
      tagColor: 'bg-blue-100 text-blue-800 border-blue-200',
      image: '/tour/step2_diagnosis.png',
      description:
        'Automated crop identification determines the plant species (e.g., Mango, Guava, Tomato, Rice, Cotton) or allows searching from 60+ pre-configured crop species.',
      highlights: [
        'Zero-shot visual crop identification via Pl@ntNet & Gemini VLM.',
        'Searchable plant database covering fruits, vegetables, pulses, & field crops.',
        'Automatic taxonomy matching to map crop-specific pathogen profiles.'
      ],
      interactiveType: 'speciesTaxonomy'
    },
    {
      id: 'diagnosis',
      title: '3. Pathogen Diagnosis & Visual Evidence',
      badge: 'Step 3 of 5',
      tag: 'Gemini VLM Multimodal Analysis',
      tagColor: 'bg-amber-100 text-amber-800 border-amber-200',
      image: '/tour/step2_diagnosis.png',
      description:
        'Gemini Vision VLM inspects physical leaf features (lesion colors, spot shapes, fungal spores, pest structures) to output structured diagnostic evidence & infection severity ratings.',
      highlights: [
        'Pathogen identification (e.g., Anthracnose, Powdery Mildew, Leaf Blight, Scale Pests).',
        'Extracts directly visible symptoms, dominant morphology, & candidate conditions.',
        'Calculates severity index ratings (Low, Moderate, Severe) & confidence scores.'
      ],
      interactiveType: 'severityGauge'
    },
    {
      id: 'treatment',
      title: '4. NACL Agrochemical Advisory & Dosage',
      badge: 'Step 4 of 5',
      tag: 'RAG Catalog Matcher',
      tagColor: 'bg-orange-100 text-[#d96b27] border-[#f5d5c0]',
      image: '/tour/step3_treatment.png',
      description:
        'RAG vector search queries NACL Industries’ official product database (59+ certified agrochemicals) to match exact chemical & biological treatment protocols.',
      highlights: [
        'Matches certified NACL fungicides, insecticides, & bio-stimulants.',
        'Calculates total product volume & water required based on field acreage.',
        'Provides application timing, spray techniques, & preventive cultural controls.'
      ],
      interactiveType: 'dosageCalc'
    },
    {
      id: 'history',
      title: '5. History, Analytics & AI Model Tuning',
      badge: 'Step 5 of 5',
      tag: 'Persistent Storage & Tuning',
      tagColor: 'bg-purple-100 text-purple-800 border-purple-200',
      image: '/tour/step4_analytics.png',
      description:
        'All diagnostic reports are saved in your MongoDB history log. You can review past runs, track farm analytics, and submit Agronomist feedback (Thumbs Up/Down) to tune the AI model.',
      highlights: [
        'Persistent database storage for instant run retrieval & PDF report exports.',
        'AI Agronomist feedback logging for dataset refinement & model tuning.',
        'Farm analytics dashboard tracking scan counts, credit usage, & crop trends.'
      ],
      interactiveType: 'pipelineFlow'
    }
  ];

  const current = tourSteps[activeStep];

  const handleNext = () => {
    if (activeStep < tourSteps.length - 1) {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (activeStep > 0) {
      setActiveStep((prev) => prev - 1);
    }
  };

  const handleStartScan = () => {
    onClose();
    navigate('/scan');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-warmgray-950/70 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-[#fcfaf7] border border-[#e8dfd1] w-full max-w-5xl max-h-[92vh] rounded-3xl shadow-2xl flex flex-col overflow-hidden text-warmgray-900">
        {/* Header Bar */}
        <div className="px-6 py-4 bg-white border-b border-[#e8dfd1] flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#d96b27] to-[#b85119] flex items-center justify-center text-white shadow-sm">
              <Sparkles className="w-5 h-5 fill-white/20" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-extrabold text-warmgray-900 tracking-tight">
                  Leaf Pathology Analysis — Guided Platform Tour
                </h2>
                <span className="px-2.5 py-0.5 rounded-full bg-[#fdeade] text-[#d96b27] text-[10px] font-mono font-bold uppercase tracking-wider">
                  Interactive Guide
                </span>
              </div>
              <p className="text-xs text-warmgray-500 font-medium">
                Step-by-step workflow to analyze plant leaves & receive NACL agrochemical treatment plans
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-warmgray-400 hover:text-warmgray-700 hover:bg-[#eae1d3]/60 transition-colors"
            title="Close guided tour"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Step Indicator Tabs Bar */}
        <div className="px-6 py-3 bg-[#f5efe6] border-b border-[#e8dfd1] flex items-center justify-between overflow-x-auto gap-2">
          {tourSteps.map((step, idx) => {
            const isActive = idx === activeStep;
            const isPassed = idx < activeStep;

            return (
              <button
                key={step.id}
                type="button"
                onClick={() => setActiveStep(idx)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-[#d96b27] text-white shadow-sm scale-[1.02]'
                    : isPassed
                    ? 'bg-[#e5ded3] text-warmgray-800 hover:bg-[#dbd3c6]'
                    : 'bg-white/80 border border-[#e5ded3] text-warmgray-500 hover:text-warmgray-800'
                }`}
              >
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-mono font-bold ${
                    isActive
                      ? 'bg-white text-[#d96b27]'
                      : isPassed
                      ? 'bg-[#d96b27] text-white'
                      : 'bg-warmgray-200 text-warmgray-600'
                  }`}
                >
                  {isPassed ? <Check className="w-3 h-3 stroke-[3]" /> : idx + 1}
                </span>
                <span>{step.title.split('.')[1].trim()}</span>
              </button>
            );
          })}
        </div>

        {/* Main Content Body */}
        <div className="flex-1 p-6 overflow-y-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Image Preview & Interactive Visualizer (6 cols) */}
          <div className="lg:col-span-6 space-y-4 flex flex-col">
            {/* Generated Step Image Container */}
            <div className="relative rounded-2xl overflow-hidden border border-[#e8dfd1] bg-warmgray-900 group shadow-md aspect-video flex items-center justify-center">
              <img
                src={current.image}
                alt={current.title}
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/20 p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold border backdrop-blur-md ${current.tagColor}`}>
                    {current.tag}
                  </span>
                  <button
                    type="button"
                    onClick={() => setZoomImage(current.image)}
                    className="p-1.5 rounded-lg bg-black/50 text-white hover:bg-black/80 backdrop-blur-md transition-all text-xs flex items-center gap-1 font-mono"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Expand Visual</span>
                  </button>
                </div>
                <div>
                  <span className="text-[10px] font-mono font-bold text-white/70 uppercase tracking-widest block">
                    AI Visual Sample
                  </span>
                  <h4 className="text-sm font-bold text-white tracking-tight">
                    {current.title}
                  </h4>
                </div>
              </div>
            </div>

            {/* Interactive Step Visualizer Card */}
            <div className="bg-white border border-[#e8dfd1] rounded-2xl p-4 space-y-3 shadow-xs flex-1 flex flex-col justify-center">
              <div className="flex items-center justify-between border-b border-warmgray-100 pb-2">
                <div className="flex items-center gap-2 text-xs font-extrabold text-warmgray-800 uppercase font-mono tracking-wider">
                  <Sliders className="w-3.5 h-3.5 text-[#d96b27]" />
                  <span>Step Interactive Simulator</span>
                </div>
                <span className="text-[10px] font-mono text-warmgray-400">Live Demo Widget</span>
              </div>

              {/* Interactive Widget 1: Quality Check Radar */}
              {current.interactiveType === 'qualityCheck' && (
                <div className="space-y-2 text-xs">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200">
                      <div className="text-[10px] font-mono text-emerald-700 font-bold">Image Resolution</div>
                      <div className="text-sm font-extrabold text-emerald-900 mt-0.5">4032 × 3024 px</div>
                      <div className="text-[10px] text-emerald-600">✓ Ultra HD Optimal</div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200">
                      <div className="text-[10px] font-mono text-emerald-700 font-bold">Focus & Clarity</div>
                      <div className="text-sm font-extrabold text-emerald-900 mt-0.5">98.4% Score</div>
                      <div className="text-[10px] text-emerald-600">✓ Sharp Edge Detection</div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200">
                      <div className="text-[10px] font-mono text-emerald-700 font-bold">Lighting Exposure</div>
                      <div className="text-sm font-extrabold text-emerald-900 mt-0.5">Normal (0.82)</div>
                      <div className="text-[10px] text-emerald-600">✓ Balanced Daylight</div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200">
                      <div className="text-[10px] font-mono text-emerald-700 font-bold">Leaf Surface Area</div>
                      <div className="text-sm font-extrabold text-emerald-900 mt-0.5">84.2% Frame</div>
                      <div className="text-[10px] text-emerald-600">✓ Centered Foliage</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Interactive Widget 2: Species Taxonomy */}
              {current.interactiveType === 'speciesTaxonomy' && (
                <div className="space-y-2.5 text-xs">
                  <div className="p-3 rounded-xl bg-[#fdf3ed] border border-[#f5d5c0] flex items-center justify-between">
                    <div>
                      <div className="text-[10px] font-mono font-bold text-[#d96b27] uppercase">Identified Plant Species</div>
                      <div className="text-sm font-extrabold text-warmgray-900">Mangifera indica (Mango)</div>
                      <div className="text-[10px] text-warmgray-500 font-mono">Family: Anacardiaceae</div>
                    </div>
                    <div className="px-3 py-1 rounded-full bg-[#d96b27] text-white text-xs font-mono font-bold shadow-xs">
                      97.8% Conf.
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-warmgray-50 border border-warmgray-200 text-[11px] space-y-1 font-mono text-warmgray-600">
                    <div className="flex justify-between"><span>Pl@ntNet Species Rank:</span> <span className="font-bold text-warmgray-800">#1 Top Match</span></div>
                    <div className="flex justify-between"><span>Database Varieties Supported:</span> <span className="font-bold text-warmgray-800">Alphonso, Dasheri, Kesar</span></div>
                  </div>
                </div>
              )}

              {/* Interactive Widget 3: Severity Heatmap & Gauge */}
              {current.interactiveType === 'severityGauge' && (
                <div className="space-y-3 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-warmgray-700">Simulate Leaf Lesion Surface Coverage:</span>
                    <span className="font-mono font-extrabold text-xs text-[#d96b27]">{lesionSlider}% Lesion</span>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="95"
                    value={lesionSlider}
                    onChange={(e) => setLesionSlider(Number(e.target.value))}
                    className="w-full accent-[#d96b27] cursor-pointer"
                  />
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className={`p-2 rounded-xl border text-[11px] font-mono font-bold ${lesionSlider < 25 ? 'bg-emerald-100 text-emerald-800 border-emerald-300' : 'bg-warmgray-50 text-warmgray-400'}`}>
                      Low (5-25%)
                    </div>
                    <div className={`p-2 rounded-xl border text-[11px] font-mono font-bold ${lesionSlider >= 25 && lesionSlider < 55 ? 'bg-amber-100 text-amber-800 border-amber-300' : 'bg-warmgray-50 text-warmgray-400'}`}>
                      Moderate (25-55%)
                    </div>
                    <div className={`p-2 rounded-xl border text-[11px] font-mono font-bold ${lesionSlider >= 55 ? 'bg-rose-100 text-rose-800 border-rose-300' : 'bg-warmgray-50 text-warmgray-400'}`}>
                      Severe (55-100%)
                    </div>
                  </div>
                </div>
              )}

              {/* Interactive Widget 4: Dosage Calculator */}
              {current.interactiveType === 'dosageCalc' && (
                <div className="space-y-2.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-warmgray-700">Select Land / Field Size (Acres):</span>
                    <div className="flex items-center gap-1.5">
                      {[1, 2, 5, 10].map((acres) => (
                        <button
                          key={acres}
                          type="button"
                          onClick={() => setFieldAcres(acres)}
                          className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all ${
                            fieldAcres === acres
                              ? 'bg-[#d96b27] text-white'
                              : 'bg-warmgray-100 text-warmgray-600 hover:bg-warmgray-200'
                          }`}
                        >
                          {acres} Acre{acres > 1 ? 's' : ''}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-orange-50/80 border border-[#f5d5c0] space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-bold text-warmgray-900">
                      <span>NACL NAGARJUNA Fungicide</span>
                      <span className="text-[#d96b27] font-mono">2.0 ml / Liter Water</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-[11px] text-warmgray-700">
                      <div className="bg-white p-2 rounded-lg border border-[#e8dfd1]">
                        <span className="text-[10px] text-warmgray-400 block">Total Product Needed:</span>
                        <span className="font-extrabold text-[#d96b27]">{fieldAcres * 500} ml</span>
                      </div>
                      <div className="bg-white p-2 rounded-lg border border-[#e8dfd1]">
                        <span className="text-[10px] text-warmgray-400 block">Water Mix Volume:</span>
                        <span className="font-extrabold text-warmgray-800">{fieldAcres * 200} Liters</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Interactive Widget 5: End-to-End Pipeline */}
              {current.interactiveType === 'pipelineFlow' && (
                <div className="space-y-2 text-xs">
                  <div className="p-2.5 rounded-xl bg-purple-50 border border-purple-200 flex items-center justify-between text-purple-900 font-mono text-[11px]">
                    <div className="flex items-center gap-1.5 font-bold">
                      <Zap className="w-3.5 h-3.5 text-purple-600" />
                      <span>Pipeline Speed:</span>
                    </div>
                    <span className="font-extrabold">~1.4 seconds complete run</span>
                  </div>
                  <div className="grid grid-cols-4 gap-1.5 text-[10px] font-mono font-bold text-center">
                    <div className="p-2 bg-warmgray-100 rounded-lg text-warmgray-700 border border-warmgray-200">1. Image Upload</div>
                    <div className="p-2 bg-warmgray-100 rounded-lg text-warmgray-700 border border-warmgray-200">2. Vision AI</div>
                    <div className="p-2 bg-warmgray-100 rounded-lg text-warmgray-700 border border-warmgray-200">3. RAG Search</div>
                    <div className="p-2 bg-purple-100 text-purple-800 rounded-lg border border-purple-300">4. Saved Run</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Step Description & Instructions (6 cols) */}
          <div className="lg:col-span-6 space-y-5 flex flex-col justify-between">
            <div className="space-y-4">
              <div>
                <span className="text-xs font-mono font-extrabold text-[#d96b27] uppercase tracking-wider block mb-1">
                  {current.badge}
                </span>
                <h3 className="text-2xl font-extrabold text-warmgray-900 tracking-tight leading-snug">
                  {current.title}
                </h3>
              </div>

              <p className="text-sm text-warmgray-700 font-medium leading-relaxed bg-white p-4 rounded-2xl border border-[#e8dfd1] shadow-xs">
                {current.description}
              </p>

              <div className="space-y-2.5">
                <h4 className="text-xs font-extrabold text-warmgray-900 uppercase font-mono tracking-wider flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-[#d96b27]" />
                  <span>Key Workflow Capabilities</span>
                </h4>
                <ul className="space-y-2">
                  {current.highlights.map((item, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2.5 p-3 rounded-xl bg-white border border-[#e8dfd1] text-xs font-medium text-warmgray-800 shadow-xs"
                    >
                      <div className="w-5 h-5 rounded-full bg-[#fdeade] text-[#d96b27] flex items-center justify-center shrink-0 mt-0.5 font-bold font-mono text-[10px]">
                        ✓
                      </div>
                      <span className="leading-relaxed">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#fdf3ed] border border-[#f5d5c0] flex items-start gap-3">
                <Info className="w-4 h-4 text-[#d96b27] shrink-0 mt-0.5" />
                <div className="text-xs text-warmgray-700 font-medium leading-relaxed">
                  <strong className="text-[#d96b27]">Pro Tip:</strong> Ensure leaf images are well-lit with clear focus on visible symptoms (spots, mildew, discoloration) for highest diagnosis accuracy.
                </div>
              </div>
            </div>

            {/* Bottom Step Navigation Bar */}
            <div className="pt-4 border-t border-[#e8dfd1] flex items-center justify-between gap-4">
              <button
                type="button"
                onClick={handlePrev}
                disabled={activeStep === 0}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all ${
                  activeStep === 0
                    ? 'opacity-40 cursor-not-allowed text-warmgray-400 border border-warmgray-200'
                    : 'bg-white border border-[#e5ded3] text-warmgray-800 hover:bg-warmgray-50'
                }`}
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Previous Step</span>
              </button>

              <span className="text-xs font-mono font-bold text-warmgray-400">
                {activeStep + 1} / {tourSteps.length}
              </span>

              {activeStep < tourSteps.length - 1 ? (
                <button
                  type="button"
                  onClick={handleNext}
                  className="flex items-center gap-2 bg-[#d96b27] hover:bg-[#c55d1d] active:scale-[0.98] text-white px-5 py-2.5 rounded-xl text-xs font-bold shadow-sm transition-all"
                >
                  <span>Next Step</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleStartScan}
                  className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 active:scale-[0.98] text-white px-6 py-2.5 rounded-xl text-xs font-bold shadow-md transition-all animate-pulse"
                >
                  <Sprout className="w-4 h-4" />
                  <span>Start Leaf Scan Now</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Image Modal Preview (Zoom) */}
      {zoomImage && (
        <div
          className="fixed inset-0 z-60 bg-black/90 flex items-center justify-center p-4 backdrop-blur-md"
          onClick={() => setZoomImage(null)}
        >
          <div className="relative max-w-4xl w-full max-h-[90vh] overflow-hidden rounded-2xl border border-warmgray-700 shadow-2xl bg-black">
            <button
              type="button"
              onClick={() => setZoomImage(null)}
              className="absolute top-4 right-4 z-10 p-2 rounded-full bg-black/60 text-white hover:bg-black transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
            <img src={zoomImage} alt="Expanded Step Visual" className="w-full h-full object-contain" />
          </div>
        </div>
      )}
    </div>
  );
};
