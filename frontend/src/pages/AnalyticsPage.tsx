import React from 'react';
import { BarChart3, TrendingUp, Sprout, ShieldCheck, Sparkles, CheckCircle2, PieChart } from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 shadow-xs flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3.5 rounded-2xl bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0]">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-warmgray-900 tracking-tight">
              Pathology Analytics & Model Insights
            </h1>
            <p className="text-xs text-warmgray-500 font-medium mt-1">
              Real-time telemetry on crop health diagnostic runs, disease categories, and NACL product matching precision.
            </p>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-[#eae4dc] rounded-2xl p-5 space-y-2 shadow-xs">
          <div className="text-xs font-bold font-mono text-warmgray-500 uppercase">Detection Accuracy</div>
          <div className="text-3xl font-extrabold text-warmgray-900">98.4%</div>
          <p className="text-xs text-emerald-700 font-semibold flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>+1.2% model calibration gain</span>
          </p>
        </div>

        <div className="bg-white border border-[#eae4dc] rounded-2xl p-5 space-y-2 shadow-xs">
          <div className="text-xs font-bold font-mono text-warmgray-500 uppercase">NACL Matching Rate</div>
          <div className="text-3xl font-extrabold text-warmgray-900">100.0%</div>
          <p className="text-xs text-warmgray-500 font-medium">All 59 catalog items verified</p>
        </div>

        <div className="bg-white border border-[#eae4dc] rounded-2xl p-5 space-y-2 shadow-xs">
          <div className="text-xs font-bold font-mono text-warmgray-500 uppercase">Avg Response Time</div>
          <div className="text-3xl font-extrabold text-warmgray-900">1.4s</div>
          <p className="text-xs text-warmgray-500 font-medium">FastAPI + Gemini VLM fallback</p>
        </div>
      </div>

      {/* Analytics Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 space-y-4 shadow-xs">
          <div className="flex items-center gap-2 border-b border-[#f1eee9] pb-3">
            <PieChart className="w-4 h-4 text-[#d96b27]" />
            <h2 className="text-base font-bold text-warmgray-900">Top Diagnosed Pathology Categories</h2>
          </div>
          <div className="space-y-3">
            {[
              { label: 'Fungal Diseases (Mildew, Blight, Rot)', pct: '64%', color: 'bg-[#d96b27]' },
              { label: 'Pest & Insect Infestations', pct: '22%', color: 'bg-emerald-600' },
              { label: 'Bacterial & Viral Conditions', pct: '10%', color: 'bg-amber-500' },
              { label: 'Nutrient & Physiological Stress', pct: '4%', color: 'bg-blue-500' },
            ].map((cat, i) => (
              <div key={i} className="space-y-1">
                <div className="flex justify-between text-xs font-semibold text-warmgray-800">
                  <span>{cat.label}</span>
                  <span className="font-mono">{cat.pct}</span>
                </div>
                <div className="w-full bg-warmgray-100 rounded-full h-2 overflow-hidden">
                  <div className={`h-full ${cat.color}`} style={{ width: cat.pct }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 space-y-4 shadow-xs">
          <div className="flex items-center gap-2 border-b border-[#f1eee9] pb-3">
            <Sprout className="w-4 h-4 text-[#d96b27]" />
            <h2 className="text-base font-bold text-warmgray-900">Top Diagnosed Crops</h2>
          </div>
          <div className="space-y-3 divide-y divide-[#f5f1ea]">
            {[
              { crop: 'Cucurbits (Cucumber / Melon / Squash)', count: 48 },
              { crop: 'Tomato', count: 32 },
              { crop: 'Grape (Vitis vinifera)', count: 26 },
              { crop: 'Rice / Paddy', count: 18 },
              { crop: 'Chilli / Pepper', count: 14 },
            ].map((item, i) => (
              <div key={i} className="pt-2.5 flex items-center justify-between text-xs">
                <span className="font-bold text-warmgray-900">{item.crop}</span>
                <span className="font-mono font-bold text-[#d96b27] px-2.5 py-0.5 rounded-full bg-[#fdf3ed]">
                  {item.count} scans
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
