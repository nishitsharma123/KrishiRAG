import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Database, 
  FileText, 
  Layers, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  MessageSquare, 
  ThumbsUp, 
  RefreshCw,
  Cpu,
  BarChart3,
  Server
} from 'lucide-react';
import { adminApi, apiService } from '../services/api';
import { useApp } from '../context/AppContext';

export const AdminPage = () => {
  const { llmStatus, health, refreshAll } = useApp();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await adminApi.getStats();
      setStats(data);
    } catch (err) {
      setError(err.message || 'Failed to retrieve administrative diagnostics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleRefresh = () => {
    fetchStats();
    refreshAll();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl lg:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Server className="w-6 h-6 text-emerald-600" />
            KrishiRAG Admin & Operational Telemetry
          </h1>
          <p className="text-xs lg:text-sm text-slate-500">
            Real-time persistence metrics, vector collection health, and query usage analytics.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs self-start sm:self-auto cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-600' : ''}`} />
          <span>Refresh System Telemetry</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Grid of Key Admin Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Total Documents & Pages */}
        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold">
            <span>Repository Corpus</span>
            <FileText className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-black text-slate-900 font-mono">
            {stats?.documents?.total ?? '—'} <span className="text-xs font-medium text-slate-500">docs</span>
          </div>
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
            <span>Pages Processed:</span>
            <span className="font-bold text-slate-900 font-mono">{stats?.documents?.total_pages?.toLocaleString() ?? '—'}</span>
          </div>
        </div>

        {/* Metric 2: Vector Chunks & Status */}
        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold">
            <span>Indexed Chunks (Qdrant)</span>
            <Layers className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-black text-slate-900 font-mono">
            {stats?.vector_store?.points_count?.toLocaleString() ?? stats?.documents?.total_chunks?.toLocaleString() ?? '—'}
          </div>
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500">Collection Status:</span>
            <span className="inline-flex items-center gap-1 font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 text-[10px]">
              <CheckCircle2 className="w-2.5 h-2.5" />
              {stats?.vector_store?.status?.toUpperCase() || 'SYNCHRONIZED'}
            </span>
          </div>
        </div>

        {/* Metric 3: Total Questions Asked */}
        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold">
            <span>User Queries Asked</span>
            <MessageSquare className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-black text-slate-900 font-mono">
            {stats?.conversations?.total_questions ?? '—'}
          </div>
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
            <span>Active Sessions:</span>
            <span className="font-bold text-slate-900 font-mono">{stats?.conversations?.total_sessions ?? '—'}</span>
          </div>
        </div>

        {/* Metric 4: Feedback Satisfaction */}
        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold">
            <span>Answer Satisfaction</span>
            <ThumbsUp className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-black text-slate-900 font-mono">
            {stats?.feedback?.satisfaction_rate ? `${stats.feedback.satisfaction_rate}%` : '100%'}
          </div>
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
            <span>Helpful Votes:</span>
            <span className="font-bold text-emerald-700 font-mono">{stats?.feedback?.positive ?? 0} / {stats?.feedback?.total ?? 0}</span>
          </div>
        </div>
      </div>

      {/* Two Detailed Technical Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Panel 1: Document Ingestion Breakdown */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <FileText className="w-4 h-4 text-emerald-600" />
            Ingestion Pipeline Status Breakdown
          </h3>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span className="font-semibold text-slate-800">Completed & Verified Ingestions</span>
              </div>
              <span className="font-mono font-bold text-emerald-700 text-sm">
                {stats?.documents?.completed ?? 0}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-500" />
                <span className="font-semibold text-slate-800">Processing / Queue</span>
              </div>
              <span className="font-mono font-bold text-amber-700 text-sm">
                {stats?.documents?.processing ?? 0}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-500" />
                <span className="font-semibold text-slate-800">Failed / Rejected Ingestions</span>
              </div>
              <span className="font-mono font-bold text-rose-700 text-sm">
                {stats?.documents?.failed ?? 0}
              </span>
            </div>
          </div>

          <div className="pt-2 text-xs text-slate-500 leading-relaxed">
            All ingested publications undergo SHA-256 duplicate rejection, PyMuPDF physical page-tracking, and heading-aware semantic chunking.
          </div>
        </div>

        {/* Panel 2: Vector & Inference Topology */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-emerald-600" />
            Vector Engine & LLM Execution Host
          </h3>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Vector Collection:</span>
              <span className="font-mono font-semibold text-slate-800">{stats?.vector_store?.collection_name}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Embedding Dimensions:</span>
              <span className="font-mono font-semibold text-slate-800">{stats?.vector_store?.vector_size || 384} (multilingual-e5-small)</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Local LLM Runtime:</span>
              <span className="font-mono font-semibold text-emerald-700">Ollama qwen3:4b (CPU-only)</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Concurrency Policy:</span>
              <span className="font-mono font-semibold text-slate-800">asyncio.Semaphore(1) Single Inference</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-500">Reranker Architecture:</span>
              <span className="font-mono font-semibold text-slate-800">ms-marco-MiniLM-L-6-v2 Cross-Encoder</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;
