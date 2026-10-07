import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Search,
  ExternalLink,
  ShieldCheck,
  Building2,
  Filter,
  CheckCircle2,
  AlertCircle,
  FlaskConical,
  Loader2
} from 'lucide-react';
import { getNaclCatalog } from '../api/leafDisease';

export const CatalogPage: React.FC = () => {
  const [catalogData, setCatalogData] = useState<{ total_count: number; categories: Record<string, any[]> } | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<string>('All');
  const [searchTerm, setSearchTerm] = useState<string>('');

  useEffect(() => {
    const fetchCatalog = async () => {
      try {
        const data = await getNaclCatalog();
        setCatalogData(data);
      } catch (err) {
        console.error('Failed to fetch NACL catalog:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchCatalog();
  }, []);

  const categoriesList = ['All', ...(catalogData?.categories ? Object.keys(catalogData.categories) : [])];

  const filteredProducts = React.useMemo(() => {
    if (!catalogData?.categories) return [];
    let list: any[] = [];
    if (activeCategory === 'All') {
      Object.values(catalogData.categories).forEach((prods) => {
        list.push(...prods);
      });
    } else {
      list = catalogData.categories[activeCategory] || [];
    }

    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      list = list.filter(
        (p) =>
          p.product_name?.toLowerCase().includes(q) ||
          p.active_ingredient?.toLowerCase().includes(q) ||
          p.category?.toLowerCase().includes(q) ||
          (p.key_benefits && p.key_benefits.some((b: string) => b.toLowerCase().includes(q)))
      );
    }
    return list;
  }, [catalogData, activeCategory, searchTerm]);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="bg-white border border-[#eae4dc] rounded-2xl p-6 shadow-xs flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3.5 rounded-2xl bg-[#fdf3ed] text-[#d96b27] border border-[#f5d5c0]">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-extrabold text-warmgray-900 tracking-tight">
                NACL Agrochemical Catalog
              </h1>
              <span className="px-2.5 py-0.5 rounded-full bg-[#fdeade] text-[#d96b27] text-xs font-bold font-mono">
                {catalogData?.total_count || 59} Verified Products
              </span>
            </div>
            <p className="text-xs text-warmgray-500 font-medium mt-1">
              Official NACL Industries database: Fungicides, Insecticides, Herbicides & Plant Growth Regulators.
            </p>
          </div>
        </div>
      </div>

      {/* Controls: Search & Category Filter Tabs */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Category Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-1 md:pb-0 scrollbar-none">
          {categoriesList.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setActiveCategory(cat)}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all shrink-0 ${
                activeCategory === cat
                  ? 'bg-[#d96b27] text-white shadow-xs'
                  : 'bg-white border border-[#e5ded3] text-warmgray-700 hover:bg-warmgray-50'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-warmgray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search product or active ingredient..."
            className="w-full bg-white border border-[#e5ded3] rounded-xl pl-9 pr-4 py-2 text-xs font-medium text-warmgray-800 focus:outline-none focus:ring-2 focus:ring-[#d96b27]/30 focus:border-[#d96b27] transition-all"
          />
        </div>
      </div>

      {/* Catalog Grid */}
      {loading ? (
        <div className="py-16 text-center space-y-3 bg-white border border-[#eae4dc] rounded-2xl">
          <Loader2 className="w-6 h-6 animate-spin text-[#d96b27] mx-auto" />
          <p className="text-xs font-bold text-warmgray-600 font-mono">Loading NACL Agrochemical Database...</p>
        </div>
      ) : filteredProducts.length === 0 ? (
        <div className="py-16 text-center space-y-2 bg-white border border-[#eae4dc] rounded-2xl">
          <p className="text-sm font-bold text-warmgray-800">No products found matching &ldquo;{searchTerm}&rdquo;</p>
          <p className="text-xs text-warmgray-500 font-mono">Try adjusting your category filter or search query.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProducts.map((prod) => (
            <div
              key={prod.product_id}
              className="bg-white border border-[#eae4dc] hover:border-[#d96b27]/40 rounded-2xl p-5 space-y-3.5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div className="space-y-2.5">
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-0.5">
                    <span className="text-[10px] font-bold font-mono text-[#d96b27] uppercase tracking-wider">
                      {prod.category}
                    </span>
                    <h3 className="text-base font-extrabold text-warmgray-900 leading-tight">
                      {prod.product_name}
                    </h3>
                  </div>
                  {prod.frac_group && (
                    <span className="px-2 py-0.5 rounded bg-warmgray-100 text-warmgray-700 text-[10px] font-mono font-bold shrink-0">
                      {prod.frac_group}
                    </span>
                  )}
                </div>

                {prod.active_ingredient && (
                  <div className="flex items-center gap-1.5 text-xs text-warmgray-700 font-semibold bg-[#fdf3ed] px-2.5 py-1 rounded-lg border border-[#f5d5c0] w-fit">
                    <FlaskConical className="w-3.5 h-3.5 text-[#d96b27]" />
                    <span>{prod.active_ingredient}</span>
                  </div>
                )}

                {prod.key_benefits && prod.key_benefits.length > 0 && (
                  <ul className="space-y-1 text-xs text-warmgray-600">
                    {prod.key_benefits.slice(0, 3).map((benefit: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                        <span className="line-clamp-2 leading-relaxed">{benefit}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="pt-3 border-t border-[#f1eee9] flex items-center justify-between text-xs">
                <span className="text-[11px] font-mono text-warmgray-400">
                  {prod.crop_applications?.length || 0} Registered Crops
                </span>
                <a
                  href={prod.product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-bold text-[#d96b27] hover:text-[#b85119] flex items-center gap-1 transition-colors"
                >
                  <span>Official Label</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
