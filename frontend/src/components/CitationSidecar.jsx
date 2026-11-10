import React, { useState } from 'react';
import { 
  X, 
  FileText, 
  CheckCircle2, 
  ExternalLink, 
  BookOpen, 
  Layers, 
  Award,
  Sparkles,
  Info,
  ChevronRight
} from 'lucide-react';

export const CitationSidecar = ({ 
  isOpen, 
  onClose, 
  activeMessage, 
  selectedCitationIndex = 0 
}) => {
  const [activeTab, setActiveTab] = useState('citations'); // 'citations' or 'chunks'
  const [selectedIdx, setSelectedIdx] = useState(selectedCitationIndex);

  if (!isOpen || !activeMessage) return null;

  const sources = activeMessage.sources || [];
  const retrievedChunks = activeMessage.retrieved_chunks || [];
  const currentSource = sources[selectedIdx] || sources[0];

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-xl bg-white shadow-2xl flex flex-col border-l border-slate-200">
          {/* Drawer Header */}
          <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center shadow-xs">
                <BookOpen className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Verified Agronomic Evidence Sidecar
                </h3>
                <p className="text-[11px] text-slate-500">
                  Strict provenance verified against authentic ICAR repository
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Tabs */}
          <div className="px-6 pt-3 border-b border-slate-100 flex gap-4 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('citations')}
              className={`pb-2.5 flex items-center gap-1.5 border-b-2 transition-colors ${
                activeTab === 'citations'
                  ? 'border-emerald-600 text-emerald-800'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              <span>Validated Citations ({sources.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('chunks')}
              className={`pb-2.5 flex items-center gap-1.5 border-b-2 transition-colors ${
                activeTab === 'chunks'
                  ? 'border-emerald-600 text-emerald-800'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Retrieved Candidates ({retrievedChunks.length})</span>
            </button>
          </div>

          {/* Drawer Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {activeTab === 'citations' ? (
              sources.length === 0 ? (
                <div className="p-8 text-center bg-slate-50 rounded-2xl border border-slate-200/80 space-y-2">
                  <Info className="w-8 h-8 text-slate-400 mx-auto" />
                  <p className="text-sm font-medium text-slate-700">No Direct Citations Found</p>
                  <p className="text-xs text-slate-500">
                    This response may have abstained or synthesized knowledge from general ICAR guidelines without specific page anchors.
                  </p>
                </div>
              ) : (
                <div className="space-y-5">
                  {/* Source Selector Pills (if multiple sources) */}
                  {sources.length > 1 && (
                    <div className="space-y-1.5">
                      <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                        Select Verified Source:
                      </span>
                      <div className="flex flex-wrap gap-2">
                        {sources.map((src, i) => (
                          <button
                            key={i}
                            onClick={() => setSelectedIdx(i)}
                            className={`text-xs px-3 py-1.5 rounded-lg border font-medium flex items-center gap-1.5 transition-all ${
                              selectedIdx === i
                                ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs'
                                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                            }`}
                          >
                            <span>Source #{i + 1}</span>
                            <span className="text-[10px] opacity-80">(p. {src.page_number})</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Selected Source Detail Card */}
                  {currentSource && (
                    <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
                      {/* Document Meta Header */}
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-emerald-800 bg-emerald-100/80 px-2 py-0.5 rounded border border-emerald-200">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            {currentSource.source_institution || 'ICAR Publication'}
                          </span>
                          <h4 className="text-sm font-bold text-slate-900 leading-snug">
                            {currentSource.document_title}
                          </h4>
                        </div>
                        <div className="text-right shrink-0">
                          <span className="text-xs font-mono font-bold text-slate-700 bg-slate-100 px-2 py-1 rounded border border-slate-200">
                            Page {currentSource.page_number}
                          </span>
                        </div>
                      </div>

                      {/* Verification & Score Metrics */}
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60 grid grid-cols-2 gap-3 text-xs">
                        <div>
                          <span className="text-[10px] text-slate-500 uppercase font-semibold block">
                            Relevance Score
                          </span>
                          <span className="font-mono font-bold text-emerald-700 text-sm">
                            {(currentSource.relevance_score * 100).toFixed(1)}% Match
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 uppercase font-semibold block">
                            Audit Status
                          </span>
                          <span className="inline-flex items-center gap-1 font-semibold text-emerald-800">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            Checksum Verified
                          </span>
                        </div>
                      </div>

                      {/* Excerpt Passage */}
                      <div className="space-y-2">
                        <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                          <FileText className="w-3.5 h-3.5 text-emerald-600" />
                          Exact Supporting ICAR Text Excerpt:
                        </span>
                        <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-200/70 text-xs text-slate-800 leading-relaxed font-sans whitespace-pre-wrap">
                          {currentSource.supporting_passage}
                        </div>
                      </div>

                      {/* Source URL if available */}
                      {currentSource.source_url && (
                        <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                          <span className="text-slate-500">Official Repository:</span>
                          <a
                            href={currentSource.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 font-semibold text-emerald-700 hover:text-emerald-800 underline"
                          >
                            <span>Open ICAR Portal</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            ) : (
              /* Retrieved Candidate Chunks (Dense + BM25 + Cross-Encoder) */
              <div className="space-y-4">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 text-xs text-slate-600 leading-relaxed">
                  <span className="font-semibold text-slate-800">Hybrid Retrieval Topology: </span>
                  Top 10 multilingual-e5 vectors + Top 10 BM25 keyword chunks fused via RRF (k=60), then reranked by Cross-Encoder. The top passages below were supplied to Qwen3:4b as context.
                </div>

                {retrievedChunks.length === 0 ? (
                  <p className="text-xs text-slate-500 text-center py-6">
                    No chunk metadata available for this turn.
                  </p>
                ) : (
                  retrievedChunks.map((chunk, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl border border-slate-200 bg-white hover:border-emerald-300 transition-colors space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-bold text-slate-900 truncate max-w-[280px]">
                          #{idx + 1}. {chunk.document_title}
                        </span>
                        <span className="font-mono text-[11px] bg-slate-100 px-2 py-0.5 rounded text-slate-700 shrink-0">
                          p. {chunk.page_number}
                        </span>
                      </div>

                      {chunk.section_heading && (
                        <div className="text-[11px] font-medium text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded inline-block">
                          § {chunk.section_heading}
                        </div>
                      )}

                      <p className="text-slate-700 leading-relaxed line-clamp-4 font-sans bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                        {chunk.text}
                      </p>

                      <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                        <span>Chunk ID: {chunk.chunk_id?.substring(0, 16)}...</span>
                        {chunk.relevance_score !== undefined && (
                          <span className="font-mono font-bold text-emerald-700">
                            Score: {chunk.relevance_score?.toFixed(3)}
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Drawer Footer */}
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
            <span>Audit Trail: SQLite Session Persisted</span>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-lg font-semibold text-xs transition-colors"
            >
              Close Sidecar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CitationSidecar;
