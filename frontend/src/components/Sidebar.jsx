import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Sprout, 
  MessageSquare, 
  FileText, 
  BarChart3, 
  Layers, 
  ShieldCheck,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { useApp } from '../context/AppContext';

export const Sidebar = ({ mobileOpen, setMobileOpen }) => {
  const { health, loadingHealth, healthError } = useApp();

  const navItems = [
    { name: 'Overview', to: '/', icon: Layers },
    { name: 'Advisory Chat', to: '/chat', icon: MessageSquare },
    { name: 'ICAR Documents', to: '/documents', icon: FileText },
    { name: 'RAG Evaluation', to: '/evaluation', icon: BarChart3 },
  ];

  const closeSidebar = () => {
    if (setMobileOpen) setMobileOpen(false);
  };

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={closeSidebar}
        />
      )}

      <aside className={`
        fixed top-0 bottom-0 left-0 z-50 w-64 bg-white border-r border-slate-200 
        flex flex-col transition-transform duration-200 ease-in-out
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Brand Header */}
        <div className="h-16 flex items-center px-6 border-b border-slate-100 gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-green-500 flex items-center justify-center text-white shadow-sm shadow-emerald-500/20">
            <Sprout className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-slate-900 tracking-tight text-lg leading-tight">
              Krishi<span className="text-emerald-600">RAG</span>
            </h1>
            <p className="text-[10px] text-slate-500 font-medium tracking-wide uppercase">
              Verifiable Agronomy OS
            </p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-4 space-y-1 flex-1">
          <div className="px-3 pb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Workspace
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={closeSidebar}
                className={({ isActive }) => `
                  flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all
                  ${isActive 
                    ? 'bg-emerald-50 text-emerald-800 font-semibold shadow-xs' 
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'}
                `}
              >
                {({ isActive }) => (
                  <>
                    <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-600' : 'text-slate-400'}`} />
                    <span>{item.name}</span>
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* System Status Footnote */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50">
          <div className="p-3 bg-white rounded-xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                Backend Core
              </span>
              {loadingHealth ? (
                <span className="inline-block w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              ) : health?.status === 'healthy' ? (
                <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  <CheckCircle2 className="w-2.5 h-2.5" /> Online
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                  <AlertTriangle className="w-2.5 h-2.5" /> Degraded
                </span>
              )}
            </div>

            <div className="space-y-1 text-[11px] text-slate-500">
              <div className="flex justify-between">
                <span>Vector Engine:</span>
                <span className="font-mono text-slate-700 font-medium">Qdrant Local</span>
              </div>
              <div className="flex justify-between">
                <span>Free Disk:</span>
                <span className="font-mono text-slate-700 font-medium">
                  {health?.system_metrics?.disk_free_gb ? `${health.system_metrics.disk_free_gb} GB` : '—'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
