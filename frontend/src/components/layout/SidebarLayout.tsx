import React, { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Sprout,
  BookOpen,
  History,
  BarChart3,
  Settings,
  Search,
  RefreshCw,
  Plus,
  Compass,
  Zap,
  ChevronsLeft,
  ChevronsRight,
  ChevronDown,
  Sparkles,
  Leaf,
  ShieldCheck
} from 'lucide-react';
import { GuidedTourModal } from '../common/GuidedTourModal';

interface SidebarLayoutProps {
  children: React.ReactNode;
}

export const SidebarLayout: React.FC<SidebarLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showTourModal, setShowTourModal] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Leaf Scanner', path: '/scan', icon: Sprout, badge: 'AI VLM' },
    { label: 'NACL Catalog', path: '/catalog', icon: BookOpen, count: '59' },
    { label: 'Scan History', path: '/history', icon: History },
    { label: 'Analytics', path: '/analytics', icon: BarChart3 },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <div className="flex min-h-screen bg-[#f8f5f0] text-warmgray-900 font-sans selection:bg-[#fdeade] selection:text-[#d96b27]">
      {/* ─── Left Sidebar ────────────────────────────────────────────────────────── */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 bg-[#f4efe6] border-r border-[#e8dfd1] flex flex-col transition-all duration-300 ${
          collapsed ? 'w-20' : 'w-64'
        }`}
      >
        {/* Brand Header */}
        <div
          className={`border-b border-[#e8dfd1]/60 flex items-center transition-all ${
            collapsed ? 'px-2 py-4 justify-between' : 'p-5 justify-between'
          }`}
        >
          <NavLink to="/" className="flex items-center gap-2.5 shrink-0 min-w-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#d96b27] to-[#b85119] flex items-center justify-center text-white shadow-sm shrink-0">
              <Leaf className="w-5 h-5 fill-white/20 text-white" />
            </div>
            {!collapsed && (
              <div className="flex flex-col min-w-0">
                <span className="font-extrabold text-base text-warmgray-900 leading-tight tracking-tight truncate">
                  Kweka AI
                </span>
                <span className="text-[11px] font-medium text-warmgray-500 truncate">
                  Assistant Platform
                </span>
              </div>
            )}
          </NavLink>
          <button
            type="button"
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg text-warmgray-400 hover:text-warmgray-700 hover:bg-[#eae1d3] transition-colors shrink-0"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronsRight className="w-4 h-4 text-[#d96b27]" /> : <ChevronsLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Section */}
        <div className="flex-1 py-6 px-3 space-y-6 overflow-y-auto">
          <div>
            {!collapsed && (
              <div className="px-3 mb-2 text-[10px] font-bold tracking-wider text-warmgray-400 uppercase font-mono">
                WORKSPACE
              </div>
            )}
            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive =
                  item.path === '/'
                    ? location.pathname === '/' || location.pathname === '/dashboard'
                    : location.pathname.startsWith(item.path);

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={`flex items-center ${collapsed ? 'justify-center px-2' : 'justify-between px-3.5'} py-2.5 rounded-xl text-sm font-semibold transition-all ${
                      isActive
                        ? 'bg-[#fdf3ed] text-[#d96b27] shadow-sm'
                        : 'text-warmgray-600 hover:bg-[#eae1d3]/60 hover:text-warmgray-900'
                    }`}
                    title={collapsed ? item.label : undefined}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <Icon className={`w-5 h-5 shrink-0 ${isActive ? 'text-[#d96b27]' : 'text-warmgray-400'}`} />
                      {!collapsed && <span className="truncate">{item.label}</span>}
                    </div>

                    {!collapsed && (
                      <div className="flex items-center gap-1.5">
                        {item.badge && (
                          <span className="px-2 py-0.5 text-[10px] font-bold font-mono rounded-full bg-[#fdeade] text-[#d96b27]">
                            {item.badge}
                          </span>
                        )}
                        {item.count && (
                          <span className="px-2 py-0.5 text-[10px] font-bold font-mono rounded-full bg-[#eae1d3] text-warmgray-600">
                            {item.count}
                          </span>
                        )}
                      </div>
                    )}
                  </NavLink>
                );
              })}
            </nav>
          </div>
        </div>

        {/* User Profile Footer */}
        <div className="p-3 border-t border-[#e8dfd1] relative">
          <button
            type="button"
            onClick={() => setUserDropdownOpen(!userDropdownOpen)}
            className={`w-full flex items-center gap-3 p-2 rounded-xl hover:bg-[#eae1d3] transition-colors text-left ${collapsed ? 'justify-center' : ''}`}
          >
            <div className="w-8 h-8 rounded-full bg-[#fdeade] border border-[#f5d5c0] flex items-center justify-center font-bold text-xs text-[#d96b27] shrink-0">
              A
            </div>
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold text-warmgray-900 truncate">Abhinav Govardhana</div>
                <div className="text-[10px] text-warmgray-500 truncate">abhinav1ras@gmail.com</div>
              </div>
            )}
            {!collapsed && <ChevronDown className="w-3.5 h-3.5 text-warmgray-400 shrink-0" />}
          </button>
        </div>
      </aside>

      {/* ─── Main Content Container ──────────────────────────────────────────────── */}
      <div className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${collapsed ? 'ml-20' : 'ml-64'}`}>
        {/* Top Header Bar */}
        <header className="sticky top-0 z-30 bg-[#f8f5f0]/90 backdrop-blur-md px-6 py-4 border-b border-[#e8dfd1]/50 flex items-center justify-between gap-4">
          {/* Global Search Input */}
          <div className="relative flex-1 max-w-md hidden md:block">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-warmgray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search diagnosis, crops, products or jump to... ⌘K"
              className="w-full bg-white border border-[#e5ded3] rounded-xl pl-9 pr-12 py-2 text-xs font-medium text-warmgray-800 placeholder:text-warmgray-400 focus:outline-none focus:ring-2 focus:ring-[#d96b27]/30 focus:border-[#d96b27] transition-all shadow-xs"
            />
            <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-mono text-warmgray-400 bg-warmgray-100 border border-warmgray-200 rounded px-1.5 py-0.5">
              ⌘K
            </kbd>
          </div>

          {/* Right Header Actions */}
          <div className="flex items-center gap-3 ml-auto">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white border border-[#e5ded3] text-xs font-bold font-mono text-warmgray-700 shadow-xs">
              <Zap className="w-3.5 h-3.5 text-[#d96b27] fill-[#d96b27]" />
              <span>100.0 Credits</span>
            </div>

            <button
              type="button"
              onClick={() => setShowTourModal(true)}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#fdeade] border border-[#f5d5c0] text-xs font-bold text-[#d96b27] hover:bg-[#fbdcc8] transition-colors shadow-xs"
            >
              <Compass className="w-3.5 h-3.5 text-[#d96b27]" />
              <span>Guided Tour</span>
            </button>

            <button
              type="button"
              onClick={() => window.location.reload()}
              className="p-2 rounded-xl bg-white border border-[#e5ded3] text-warmgray-600 hover:text-warmgray-900 hover:bg-warmgray-50 transition-colors shadow-xs"
              title="Refresh platform status"
            >
              <RefreshCw className="w-4 h-4" />
            </button>

            <button
              type="button"
              onClick={() => navigate('/scan')}
              className="flex items-center gap-2 bg-[#d96b27] hover:bg-[#c55d1d] active:scale-[0.98] text-white px-4 py-2 rounded-xl text-xs font-bold shadow-sm transition-all"
            >
              <Plus className="w-4 h-4" />
              <span>New Scan</span>
            </button>
          </div>
        </header>

        {/* Page Content Body */}
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto space-y-8">
          {children}
        </main>
      </div>

      {/* Guided Tour Modal */}
      <GuidedTourModal isOpen={showTourModal} onClose={() => setShowTourModal(false)} />
    </div>
  );
};

