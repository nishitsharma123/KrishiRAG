import React from 'react';
import { 
  BarChart3, 
  CheckCircle2, 
  Target, 
  ShieldCheck, 
  BookOpen, 
  Cpu, 
  Info
} from 'lucide-react';

export const EvaluationPage = () => {
  const plannedMetrics = [
    {
      name: 'Context Recall (Hit Rate @ 5)',
      description: 'Percentage of authentic ICAR test questions where the ground-truth advisory passage is present in the top 5 reranked context chunks.',
      target: '≥ 92%',
      status: 'Target Standard'
    },
    {
      name: 'Context Precision (MRR)',
      description: 'Mean Reciprocal Rank evaluating how high the most relevant ICAR source passage ranks among candidate chunks.',
      target: '≥ 0.85',
      status: 'Target Standard'
    },
    {
      name: 'Faithfulness (Zero Hallucination)',
      description: 'Ratio of statements in the Qwen3 response that can be mathematically inferred directly from the retrieved context passages.',
      target: '≥ 95%',
      status: 'Strict Constraint'
    },
    {
      name: 'Citation Precision',
      description: 'Percentage of response citations whose documented page number and excerpt passage correspond exactly to the underlying ICAR publication.',
      target: '100%',
      status: 'Zero-Tolerance Policy'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-xl lg:text-2xl font-bold text-slate-900 tracking-tight">
          RAG Quality & Benchmark Evaluation
        </h1>
        <p className="text-xs lg:text-sm text-slate-500">
          Evaluation framework adhering to RAGAS and custom ICAR agricultural verification metrics.
        </p>
      </div>

      {/* Info Notice */}
      <div className="p-4 rounded-xl bg-emerald-50/80 border border-emerald-200 flex items-start gap-3">
        <Info className="w-5 h-5 text-emerald-700 shrink-0 mt-0.5" />
        <div className="text-xs text-emerald-900 leading-relaxed">
          <span className="font-bold">Evaluation Phase Status: </span>
          The formal evaluation benchmark execution is scheduled for <strong>Phase 6</strong>. 
          The metrics engine will ingest a curated agricultural QA evaluation dataset containing ground-truth questions, 
          ICAR manual page references, and chemical dosage standards to rigorously score retrieval and generation faithfulness.
        </div>
      </div>

      {/* Metrics Standard Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {plannedMetrics.map((m, idx) => (
          <div key={idx} className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Target className="w-4 h-4 text-emerald-600" />
                {m.name}
              </h3>
              <span className="text-[10px] font-semibold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">
                {m.status}
              </span>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              {m.description}
            </p>
            <div className="pt-2 flex items-center justify-between border-t border-slate-100 text-xs">
              <span className="text-slate-500 font-medium">Evaluation Threshold:</span>
              <span className="font-mono font-bold text-emerald-700">{m.target}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Architecture Verification Protocol */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-3">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          Negative Constraint & Fallback Validation
        </h3>
        <p className="text-xs text-slate-600 leading-relaxed">
          In addition to positive recall benchmarks, KrishiRAG tests adversarial out-of-domain queries 
          (e.g., non-agricultural questions, unverified home remedies, unapproved chemical cocktails). 
          The system passes only if it declines to answer and produces the standard negative fallback:
        </p>
        <div className="p-3 bg-slate-900 text-emerald-400 font-mono text-xs rounded-xl border border-slate-800">
          "The available ICAR documentation does not provide verified guidelines for this query."
        </div>
      </div>
    </div>
  );
};
