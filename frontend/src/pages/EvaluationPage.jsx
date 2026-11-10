import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  CheckCircle2, 
  Target, 
  ShieldCheck, 
  BookOpen, 
  Clock, 
  Info,
  RefreshCw,
  Search,
  AlertCircle
} from 'lucide-react';
import { evaluationApi } from '../services/api';

export const EvaluationPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterCrop, setFilterCrop] = useState('');

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await evaluationApi.getMetrics();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load evaluation metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const benchmarkQueries = data?.benchmark_queries || [];
  const filteredQueries = filterCrop 
    ? benchmarkQueries.filter((q) => q.crop.toLowerCase() === filterCrop.toLowerCase())
    : benchmarkQueries;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl lg:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-emerald-600" />
            RAG Quality & Benchmark Evaluation Dashboard
          </h1>
          <p className="text-xs lg:text-sm text-slate-500">
            Empirical benchmark metrics evaluating hybrid retrieval recall, MRR, citation precision, and RAGAS standards.
          </p>
        </div>

        <button
          onClick={fetchMetrics}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs self-start sm:self-auto cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-600' : ''}`} />
          <span>Refresh Benchmark Data</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {loading ? (
          <div className="col-span-full p-8 text-center text-xs text-slate-500">
            <RefreshCw className="w-5 h-5 animate-spin mx-auto text-emerald-600 mb-2" />
            Loading benchmark calculations...
          </div>
        ) : (
          data?.aggregate_metrics?.map((m) => (
            <div
              key={m.key}
              className={`p-5 rounded-2xl border shadow-xs space-y-2.5 transition-all ${
                m.is_calculated
                  ? 'bg-white border-slate-200'
                  : 'bg-slate-50/80 border-slate-200/60 opacity-80'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700">{m.name}</span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                    m.status === 'PASSED' || m.status === 'ACTIVE'
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      : 'bg-amber-100 text-amber-800 border border-amber-200'
                  }`}
                >
                  {m.status === 'PENDING_PHASE_6' ? 'Phase 6' : m.status}
                </span>
              </div>

              <div className="text-2xl font-black text-slate-900 font-mono">
                {m.value}
              </div>

              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-slate-400 font-medium">Target: {m.target}</span>
                <span className="text-[11px] font-semibold text-slate-600">
                  {m.is_calculated ? 'Empirical' : 'RAGAS Judge'}
                </span>
              </div>

              <p className="text-[11px] text-slate-500 leading-snug">
                {m.description}
              </p>
            </div>
          ))
        )}
      </div>

      {/* Ground-Truth Evaluation Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Target className="w-4 h-4 text-emerald-600" />
              15 Agricultural Ground-Truth Benchmark Queries (Phase 3 Verified)
            </h3>
            <p className="text-xs text-slate-500">
              Evaluated against authentic ICAR publications across Wheat, Rice, and Mustard.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Filter Crop:</span>
            <select
              value={filterCrop}
              onChange={(e) => setFilterCrop(e.target.value)}
              className="px-2.5 py-1 rounded-lg border border-slate-200 text-xs font-semibold text-slate-800 bg-slate-50 focus:outline-none"
            >
              <option value="">All Crops</option>
              <option value="Wheat">Wheat</option>
              <option value="Rice">Rice</option>
              <option value="Mustard">Mustard</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
              <tr>
                <th className="px-5 py-3.5">#</th>
                <th className="px-5 py-3.5">Ground-Truth Query</th>
                <th className="px-4 py-3.5">Crop</th>
                <th className="px-5 py-3.5">Top Retrieved ICAR Doc</th>
                <th className="px-3 py-3.5 text-center">Page</th>
                <th className="px-3 py-3.5 text-center font-mono">P@5</th>
                <th className="px-3 py-3.5 text-center font-mono">R@5</th>
                <th className="px-3 py-3.5 text-center font-mono">MRR</th>
                <th className="px-4 py-3.5 text-right font-mono">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredQueries.map((q) => (
                <tr key={q.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-5 py-3.5 font-mono text-slate-400">{q.id}</td>
                  <td className="px-5 py-3.5 font-medium text-slate-900 max-w-xs leading-snug">
                    {q.query}
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="inline-block text-[10px] font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      {q.crop}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-slate-700 max-w-xs truncate" title={q.top_doc}>
                    {q.top_doc}
                  </td>
                  <td className="px-3 py-3.5 text-center font-mono font-bold text-slate-800">
                    p. {q.page}
                  </td>
                  <td className="px-3 py-3.5 text-center font-mono text-emerald-700 font-bold">
                    {(q.p_at_5 * 100).toFixed(0)}%
                  </td>
                  <td className="px-3 py-3.5 text-center font-mono text-emerald-700 font-bold">
                    {(q.r_at_5 * 100).toFixed(0)}%
                  </td>
                  <td className="px-3 py-3.5 text-center font-mono text-emerald-700 font-bold">
                    {q.mrr.toFixed(3)}
                  </td>
                  <td className="px-4 py-3.5 text-right font-mono text-slate-600">
                    {q.latency_ms.toFixed(0)} ms
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default EvaluationPage;
