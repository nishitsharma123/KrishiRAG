import React from 'react';
import { Menu, BookOpen, Cpu, RefreshCw, Sparkles, AlertCircle } from 'lucide-react';
import { useApp } from '../context/AppContext';

export const Header = ({ setMobileOpen }) => {
  const { health, loadingHealth, llmStatus, loadingLLM, refreshAll } = useApp();

  return (
    <header className="h-16 bg-white/90 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30 px-4 lg:px-8 flex items-center justify-between shadow-xs">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setMobileOpen(true)}
          className="p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 lg:hidden"
          aria-label="Open sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-emerald-100/80 text-emerald-800 border border-emerald-200">
            ICAR / SAU Official Publications Only
          </span>
          <span className="hidden md:inline-flex text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            Deterministic Grounding
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Ollama / Qwen3 Status Pill */}
        <div className="flex items-center gap-2 text-xs px-2.5 py-1.5 rounded-lg border bg-slate-50 border-slate-200">
          {loadingLLM ? (
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          ) : llmStatus?.system_ready ? (
            <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-xs shadow-emerald-500/50" />
          ) : (
            <span className="w-2 h-2 rounded-full bg-rose-500" />
          )}
          <span className="font-medium text-slate-700">
            {llmStatus?.system_ready
              ? 'Qwen3:4b Active'
              : llmStatus?.ollama_available
              ? 'Model Loading...'
              : 'Ollama Offline'}
          </span>
          <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">(CPU)</span>
        </div>

        {/* Hardware Architecture Pill */}
        <div className="hidden lg:flex items-center gap-2 text-xs text-slate-600 bg-slate-100/70 px-3 py-1.5 rounded-lg border border-slate-200/60 font-medium">
          <Cpu className="w-3.5 h-3.5 text-slate-500" />
          <span>Local Qdrant + BM25 Hybrid</span>
        </div>

        {/* Refresh Status Button */}
        <button
          onClick={refreshAll}
          disabled={loadingHealth || loadingLLM}
          title="Refresh Backend & LLM Status"
          className="p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${(loadingHealth || loadingLLM) ? 'animate-spin text-emerald-600' : ''}`} />
        </button>
      </div>
    </header>
  );
};
