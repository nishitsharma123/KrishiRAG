import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Sprout, 
  ArrowRight, 
  ShieldCheck, 
  FileCheck2, 
  Cpu, 
  Search, 
  Database,
  CheckCircle2,
  AlertCircle,
  Bot
} from 'lucide-react';
import { useApp } from '../context/AppContext';

export const LandingPage = () => {
  const { health, loadingHealth, healthError, llmStatus, loadingLLM } = useApp();

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-emerald-900 via-emerald-800 to-green-950 text-white p-8 lg:p-12 shadow-xl shadow-emerald-950/10">
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-700/60 border border-emerald-500/30 text-emerald-200 text-xs font-medium">
            <Sprout className="w-3.5 h-3.5 text-emerald-400" />
            Empowering Precision Agronomy with Zero Hallucinations
          </div>

          <h1 className="text-3xl lg:text-5xl font-extrabold tracking-tight leading-tight">
            Evidence-Grounded Agricultural Advisory Operating System
          </h1>

          <p className="text-emerald-100/90 text-sm lg:text-base leading-relaxed">
            KrishiRAG provides farmers and agronomists with answers derived exclusively from verified 
            Indian Council of Agricultural Research (ICAR) packages of practices and university publications. 
            Every recommendation is guaranteed traceable down to the original document and page number.
          </p>

          <div className="pt-2 flex flex-wrap gap-4">
            <Link
              to="/chat"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white text-emerald-900 font-semibold text-sm hover:bg-emerald-50 transition-colors shadow-md"
            >
              Open Advisory Chat
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              to="/documents"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-700/60 hover:bg-emerald-700/80 text-white border border-emerald-500/40 font-semibold text-sm transition-colors"
            >
              Browse ICAR Documents
            </Link>
          </div>
        </div>

        {/* Decorative background glow */}
        <div className="absolute -right-20 -bottom-20 w-80 h-80 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />
      </div>

      {/* Live System Diagnostics Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <Database className="w-4 h-4 text-emerald-600" />
            Backend & Model Pipeline Diagnostics
          </h2>
          <span className="text-xs text-slate-500">Live API Polling</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: FastAPI Core */}
          <div className="p-5 rounded-xl bg-white border border-slate-200/80 shadow-xs space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>FastAPI Backend</span>
              {loadingHealth ? (
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              ) : health?.status === 'healthy' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-500" />
              )}
            </div>
            <div className="text-xl font-bold text-slate-900">
              {loadingHealth ? 'Checking...' : health?.status?.toUpperCase() || 'OFFLINE'}
            </div>
            <div className="text-xs text-slate-500">
              Version: <span className="font-mono text-slate-700 font-medium">{health?.version || '1.0.0'}</span>
            </div>
          </div>

          {/* Card 2: Qwen3 LLM */}
          <div className="p-5 rounded-xl bg-white border border-slate-200/80 shadow-xs space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Qwen3:4b (Ollama)</span>
              {loadingLLM ? (
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              ) : llmStatus?.system_ready ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-500" />
              )}
            </div>
            <div className="text-xl font-bold text-slate-900">
              {loadingLLM ? 'Checking...' : llmStatus?.system_ready ? 'ONLINE' : 'DEGRADED'}
            </div>
            <div className="text-xs text-slate-500">
              Runtime: <span className="font-mono text-slate-700 font-medium">{llmStatus?.model_name || 'qwen3:4b'} (CPU)</span>
            </div>
          </div>

          {/* Card 3: Vector Storage */}
          <div className="p-5 rounded-xl bg-white border border-slate-200/80 shadow-xs space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Vector Database</span>
              <Search className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-xl font-bold text-slate-900">
              Qdrant Local
            </div>
            <div className="text-xs text-slate-500 truncate" title={health?.vector_db_path}>
              Collection: <span className="font-mono text-slate-700 font-medium">icar_knowledge</span>
            </div>
          </div>

          {/* Card 4: Database Connectivity */}
          <div className="p-5 rounded-xl bg-white border border-slate-200/80 shadow-xs space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Metadata Database</span>
              <Database className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-xl font-bold text-slate-900">
              {health?.database_connected ? 'CONNECTED' : 'DISCONNECTED'}
            </div>
            <div className="text-xs text-slate-500">
              Engine: <span className="font-mono text-slate-700 font-medium">SQLite (WAL Mode)</span>
            </div>
          </div>
        </div>

        {healthError && (
          <div className="mt-3 p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>Connection Warning: {healthError}. Verify that the FastAPI backend is running on port 8000.</span>
          </div>
        )}
      </div>

      {/* Core Architectural Pillars */}
      <div>
        <h2 className="text-base font-bold text-slate-800 mb-4">
          System Guarantees & Operating Principles
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-xl bg-white border border-slate-200/80 shadow-xs space-y-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <FileCheck2 className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-base">Verifiable Page Provenance</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Every chemical dosage and agronomic recommendation is tethered to exact page citations. 
              The system rejects answers if supporting passages cannot be retrieved from indexed documents.
            </p>
          </div>

          <div className="p-6 rounded-xl bg-white border border-slate-200/80 shadow-xs space-y-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <Search className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-base">Hybrid Dense-Sparse Search</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Combines BM25 keyword matching for exact chemical formulas and pest nomenclature with 
              multilingual E5 dense embeddings for vernacular regional agricultural queries.
            </p>
          </div>

          <div className="p-6 rounded-xl bg-white border border-slate-200/80 shadow-xs space-y-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-base">CPU-First Edge Architecture</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Tailored for AMD Ryzen 5 5500U and 8 GB RAM. Operates without Docker containers or external GPUs, 
              maintaining an efficient memory footprint with Ollama Qwen3 4B.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
