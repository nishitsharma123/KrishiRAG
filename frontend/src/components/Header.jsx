import React from 'react';
import { Menu, BookOpen, Cpu, RefreshCw } from 'lucide-react';
import { useApp } from '../context/AppContext';

export const Header = ({ setMobileOpen }) => {
  const { health, loadingHealth, refreshHealth } = useApp();

  return (
    <header className="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30 px-4 lg:px-8 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setMobileOpen(true)}
          className="p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 lg:hidden"
          aria-label="Open sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-emerald-100/70 text-emerald-800 border border-emerald-200/80">
            ICAR / Govt. Verified Sources Only
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Hardware & Diagnostic Pill */}
        <div className="hidden sm:flex items-center gap-3 text-xs text-slate-600 bg-slate-100/80 px-3 py-1.5 rounded-lg border border-slate-200/60">
          <div className="flex items-center gap-1.5 font-medium">
            <Cpu className="w-3.5 h-3.5 text-slate-500" />
            <span>Ryzen 5 5500U Profile (CPU Only)</span>
          </div>
          <span className="text-slate-300">|</span>
          <div className="flex items-center gap-1.5 font-medium">
            <BookOpen className="w-3.5 h-3.5 text-emerald-600" />
            <span>Strict Provenance Active</span>
          </div>
        </div>

        {/* Refresh Status Button */}
        <button
          onClick={refreshHealth}
          disabled={loadingHealth}
          title="Refresh Backend Diagnostic Status"
          className="p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loadingHealth ? 'animate-spin text-emerald-600' : ''}`} />
        </button>
      </div>
    </header>
  );
};
