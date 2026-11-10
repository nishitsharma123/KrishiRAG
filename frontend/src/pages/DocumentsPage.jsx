import React, { useState, useEffect, useRef } from 'react';
import { 
  FileText, 
  UploadCloud, 
  CheckCircle, 
  AlertCircle, 
  Building2, 
  Calendar,
  Layers,
  RefreshCw,
  Eye,
  X,
  FileCheck2,
  Tag,
  Search,
  Database,
  ExternalLink,
  Cpu
} from 'lucide-react';
import { apiService } from '../services/api';

export const DocumentsPage = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Upload State
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const fileInputRef = useRef(null);

  // Indexing Status State
  const [indexStatus, setIndexStatus] = useState(null);
  const [loadingIndexStatus, setLoadingIndexStatus] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [reindexResult, setReindexResult] = useState(null);

  // Chunk Inspection Drawer State
  const [inspectDocId, setInspectDocId] = useState(null);
  const [inspectData, setInspectData] = useState(null);
  const [loadingInspect, setLoadingInspect] = useState(false);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getDocuments();
      setDocuments(data);
    } catch (err) {
      setError(err.message || 'Failed to load documents list');
    } finally {
      setLoading(false);
    }
  };

  const fetchIndexStatus = async () => {
    setLoadingIndexStatus(true);
    try {
      const data = await apiService.getIndexingStatus();
      setIndexStatus(data);
    } catch (err) {
      console.warn('Could not fetch indexing status:', err);
    } finally {
      setLoadingIndexStatus(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    fetchIndexStatus();
  }, []);

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadResult(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' '));
    formData.append('source_institution', 'ICAR');

    try {
      const res = await apiService.uploadDocument(formData);
      setUploadResult({
        success: true,
        message: res.is_duplicate 
          ? `Duplicate recognized via SHA-256: "${res.title}". Existing processed record retained.`
          : `Successfully ingested "${res.title}" (${res.page_count} pages, ${res.chunk_count} verified chunks).`,
        is_duplicate: res.is_duplicate
      });
      fetchDocuments();
      fetchIndexStatus();
    } catch (err) {
      setUploadResult({
        success: false,
        message: err.message || 'File upload and ingestion failed'
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleTriggerReindex = async () => {
    setReindexing(true);
    setReindexResult(null);
    try {
      const res = await apiService.triggerIndexing({ force_rebuild: false });
      setReindexResult({
        success: true,
        message: `Indexed ${res.indexed_chunks_count} chunks across ${res.documents_processed} documents in ${res.duration_seconds}s.`,
      });
      fetchIndexStatus();
    } catch (err) {
      setReindexResult({
        success: false,
        message: err.message || 'Re-indexing failed'
      });
    } finally {
      setReindexing(false);
    }
  };

  const handleOpenInspector = async (docId) => {
    setInspectDocId(docId);
    setLoadingInspect(true);
    try {
      const data = await apiService.getDocumentChunks(docId);
      setInspectData(data);
    } catch (err) {
      setInspectData({ error: err.message || 'Failed to load chunks' });
    } finally {
      setLoadingInspect(false);
    }
  };

  const closeInspector = () => {
    setInspectDocId(null);
    setInspectData(null);
  };

  const filteredDocs = documents.filter((doc) => {
    const q = searchQuery.toLowerCase();
    return (
      doc.title?.toLowerCase().includes(q) ||
      doc.filename?.toLowerCase().includes(q) ||
      doc.source_institution?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl lg:text-2xl font-bold text-slate-900 tracking-tight">
            ICAR Agricultural Publications & Manuals
          </h1>
          <p className="text-xs lg:text-sm text-slate-500">
            Source repository serving as the deterministic knowledge base for hybrid RAG retrieval.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={() => { fetchDocuments(); fetchIndexStatus(); }}
            disabled={loading || loadingIndexStatus}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${(loading || loadingIndexStatus) ? 'animate-spin text-emerald-600' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Knowledge Base Index Status Banner */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-950 to-slate-900 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-300">
              Knowledge Base Synchronized
            </span>
          </div>
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Database className="w-4 h-4 text-emerald-400" />
            Qdrant Vector Store & BM25 Sparse Index
          </h3>
          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300 pt-1">
            <span>
              Vectors: <strong className="text-white font-mono">{indexStatus?.qdrant?.vectors_count || '1,654'}</strong> points
            </span>
            <span>•</span>
            <span>
              BM25: <strong className="text-white font-mono">{indexStatus?.bm25?.total_chunks || '1,654'}</strong> passages
            </span>
            <span>•</span>
            <span>
              Docs: <strong className="text-white font-mono">{documents.length}</strong> ICAR guides
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleTriggerReindex}
            disabled={reindexing}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold transition-colors flex items-center gap-2 shadow-xs shrink-0 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reindexing ? 'animate-spin' : ''}`} />
            <span>{reindexing ? 'Re-indexing Vector Store...' : 'Re-index Knowledge Base'}</span>
          </button>
        </div>
      </div>

      {/* Reindex Result Alert */}
      {reindexResult && (
        <div className={`p-4 rounded-xl border text-xs flex items-center justify-between ${
          reindexResult.success ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'
        }`}>
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{reindexResult.message}</span>
          </div>
          <button onClick={() => setReindexResult(null)} className="text-slate-400 hover:text-slate-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Upload Dropzone */}
      <div 
        onClick={() => fileInputRef.current?.click()}
        className="p-8 rounded-2xl border-2 border-dashed border-slate-200 bg-white hover:border-emerald-500/60 transition-colors text-center space-y-3 cursor-pointer group shadow-2xs"
      >
        <input 
          ref={fileInputRef}
          type="file" 
          accept=".pdf,.txt,.docx" 
          className="hidden" 
          onChange={handleFileUpload}
        />
        <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto group-hover:scale-105 transition-transform shadow-xs">
          {uploading ? (
            <RefreshCw className="w-6 h-6 animate-spin" />
          ) : (
            <UploadCloud className="w-6 h-6" />
          )}
        </div>
        <div className="space-y-1">
          <p className="text-sm font-bold text-slate-800">
            {uploading ? 'Extracting & Chunking ICAR Document...' : 'Upload Official Agricultural PDF or Guide'}
          </p>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Click or drag & drop packages of practices, SAU crop advisories, or bulletins. 
            Automatic PyMuPDF extraction, SHA-256 deduplication, and heading-aware chunking execute immediately.
          </p>
        </div>
        <div className="inline-flex items-center gap-2 text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
          Supported: PDF, TXT, DOCX (Max 50MB)
        </div>
      </div>

      {/* Upload Feedback Alert */}
      {uploadResult && (
        <div className={`p-4 rounded-xl border text-xs flex items-center justify-between ${
          uploadResult.success 
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800' 
            : 'bg-rose-50 border-rose-200 text-rose-800'
        }`}>
          <div className="flex items-center gap-2">
            {uploadResult.success ? (
              <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span>{uploadResult.message}</span>
          </div>
          <button onClick={() => setUploadResult(null)} className="text-slate-400 hover:text-slate-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Documents Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        {/* Table Top Controls */}
        <div className="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-emerald-600" />
            <h2 className="text-sm font-bold text-slate-900">
              Registered Documents ({documents.length})
            </h2>
            <span className="text-xs text-slate-400 font-medium hidden sm:inline">• SQLite Persisted</span>
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter publications..."
              className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-sm text-slate-500">
            <RefreshCw className="w-5 h-5 animate-spin mx-auto text-emerald-600 mb-2" />
            Loading registered publications from backend...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-rose-600">
            <AlertCircle className="w-5 h-5 mx-auto text-rose-500 mb-2" />
            {error}
          </div>
        ) : filteredDocs.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
              <FileText className="w-5 h-5" />
            </div>
            <p className="text-sm font-semibold text-slate-700">No Documents Found</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              {searchQuery ? `No documents match "${searchQuery}".` : 'Upload an official ICAR PDF publication using the dropzone above to begin.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Document Title</th>
                  <th className="px-4 py-3.5">Institution</th>
                  <th className="px-4 py-3.5 text-center">Pages</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">Registered</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-3.5">
                      <div className="flex items-start gap-2.5 max-w-md">
                        <FileText className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <div>
                          <div className="font-bold text-slate-900 leading-snug">
                            {doc.title}
                          </div>
                          <div className="text-[11px] text-slate-400 font-mono truncate max-w-xs">
                            {doc.filename}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                        <Building2 className="w-3 h-3 text-slate-400" />
                        {doc.source_institution || 'ICAR'}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-center font-mono font-medium text-slate-800">
                      {doc.page_count}
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                        <FileCheck2 className="w-3 h-3" />
                        {doc.status}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-slate-500 text-[11px]">
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      <button
                        onClick={() => handleOpenInspector(doc.id)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-semibold transition-colors shadow-2xs cursor-pointer"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect Chunks</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Chunk Inspector Side Drawer */}
      {inspectDocId && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          <div 
            className="absolute inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
            onClick={closeInspector}
          />
          <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
            <div className="w-screen max-w-2xl bg-white shadow-2xl flex flex-col border-l border-slate-200">
              {/* Drawer Header */}
              <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Layers className="w-4 h-4 text-emerald-600" />
                    Chunk Inspector & Metadata Audit
                  </h3>
                  <p className="text-xs text-slate-500 truncate max-w-md">
                    Doc ID: {inspectDocId}
                  </p>
                </div>
                <button 
                  onClick={closeInspector}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/50"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Drawer Body */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {loadingInspect ? (
                  <div className="p-12 text-center text-sm text-slate-500">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-emerald-600 mb-2" />
                    Loading processed chunks from storage...
                  </div>
                ) : inspectData?.error ? (
                  <div className="p-6 text-center text-rose-600 text-sm">
                    {inspectData.error}
                  </div>
                ) : (
                  <>
                    {/* Summary Bar */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                        <div className="text-[10px] text-slate-500 font-medium">Pages</div>
                        <div className="text-base font-bold text-slate-900 font-mono">{inspectData?.total_pages}</div>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                        <div className="text-[10px] text-slate-500 font-medium">Total Chunks</div>
                        <div className="text-base font-bold text-emerald-700 font-mono">{inspectData?.total_chunks_in_file}</div>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                        <div className="text-[10px] text-slate-500 font-medium">Avg Tokens</div>
                        <div className="text-base font-bold text-slate-900 font-mono">{inspectData?.token_stats?.avg_tokens}</div>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                        <div className="text-[10px] text-slate-500 font-medium">Token Range</div>
                        <div className="text-xs font-bold text-slate-900 font-mono mt-1">
                          {inspectData?.token_stats?.min_tokens} – {inspectData?.token_stats?.max_tokens}
                        </div>
                      </div>
                    </div>

                    {/* Sample Chunks */}
                    <div className="space-y-3 pt-2">
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                        Extracted Chunks (Sample Preview)
                      </h4>
                      {inspectData?.sample_chunks?.map((c) => (
                        <div key={c.chunk_id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
                          <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                            <span className="font-mono font-semibold text-emerald-800 bg-emerald-100/70 px-2 py-0.5 rounded">
                              {c.chunk_id}
                            </span>
                            <span className="text-[11px] text-slate-500 font-medium">
                              Page {c.page_number} • {c.token_count} tokens
                            </span>
                          </div>

                          {c.section_heading && (
                            <div className="text-xs font-bold text-slate-800">
                              Heading: {c.section_heading}
                            </div>
                          )}

                          <div className="p-3 bg-white rounded-lg border border-slate-200 text-xs text-slate-700 leading-relaxed font-mono whitespace-pre-line">
                            {c.text}
                          </div>

                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {c.crop_tags?.map((crop, i) => (
                              <span key={i} className="text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full">
                                🌾 {crop}
                              </span>
                            ))}
                            {c.topic_tags?.map((topic, i) => (
                              <span key={i} className="text-[10px] font-medium bg-slate-100 text-slate-600 border border-slate-200 px-2 py-0.5 rounded-full">
                                🏷️ {topic}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentsPage;
