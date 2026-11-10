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
  Tag
} from 'lucide-react';
import { apiService } from '../services/api';

export const DocumentsPage = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Upload State
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const fileInputRef = useRef(null);

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

  useEffect(() => {
    fetchDocuments();
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
          ? `Duplicate file recognized via SHA-256: "${res.title}". Processed instance retrieved.`
          : `Successfully ingested "${res.title}" (${res.page_count} pages, ${res.chunk_count} verified chunks).`,
        is_duplicate: res.is_duplicate
      });
      fetchDocuments();
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

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl lg:text-2xl font-bold text-slate-900 tracking-tight">
            ICAR Agricultural Publications & Manuals
          </h1>
          <p className="text-xs lg:text-sm text-slate-500">
            Source documents serving as the deterministic knowledge base for RAG retrieval.
          </p>
        </div>

        <button
          onClick={fetchDocuments}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-600' : ''}`} />
          Refresh Registry
        </button>
      </div>

      {/* Upload Dropzone */}
      <div 
        onClick={() => fileInputRef.current?.click()}
        className="p-8 rounded-2xl border-2 border-dashed border-slate-200 bg-white hover:border-emerald-500/60 transition-colors text-center space-y-3 cursor-pointer group"
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
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <FileText className="w-4 h-4 text-emerald-600" />
            Registered Documents ({documents.length})
          </h2>
          <span className="text-xs text-slate-500">Persisted in SQLite</span>
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
        ) : documents.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
              <FileText className="w-5 h-5" />
            </div>
            <p className="text-sm font-semibold text-slate-700">No Documents Uploaded Yet</p>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Upload an ICAR PDF above to inspect chunking and page provenance.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3">Document Title</th>
                  <th className="px-6 py-3">Institution</th>
                  <th className="px-6 py-3">Pages</th>
                  <th className="px-6 py-3">Chunks</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-3.5 font-medium text-slate-900">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-emerald-600 shrink-0" />
                        <div>
                          <div className="font-semibold text-slate-900">{doc.title}</div>
                          <div className="text-[10px] text-slate-400 font-mono truncate max-w-xs">{doc.filename}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-3.5 text-slate-600">
                      <span className="inline-flex items-center gap-1">
                        <Building2 className="w-3 h-3 text-slate-400" />
                        {doc.source_institution || 'ICAR'}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 font-mono text-slate-600">
                      {doc.page_count || '—'}
                    </td>
                    <td className="px-6 py-3.5 font-mono font-semibold text-emerald-700">
                      {doc.chunk_count || '—'}
                    </td>
                    <td className="px-6 py-3.5">
                      <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${
                        doc.status === 'COMPLETED' 
                          ? 'text-emerald-700 bg-emerald-50 border-emerald-200' 
                          : doc.status === 'PROCESSING'
                          ? 'text-amber-700 bg-amber-50 border-amber-200'
                          : 'text-rose-700 bg-rose-50 border-rose-200'
                      }`}>
                        <CheckCircle className="w-3 h-3" />
                        {doc.status}
                      </span>
                    </td>
                    <td className="px-6 py-3.5">
                      <button
                        onClick={() => handleOpenInspector(doc.id)}
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-700 hover:text-emerald-700 px-2.5 py-1 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        Inspect Chunks
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Chunk Inspector Side Drawer / Modal */}
      {inspectDocId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-4xl w-full max-h-[85vh] flex flex-col overflow-hidden animate-fadeIn">
            {/* Drawer Header */}
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div>
                <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                  <FileCheck2 className="w-4 h-4 text-emerald-600" />
                  Chunk Inspector: {inspectData?.document_title || 'Document'}
                </h3>
                <p className="text-[11px] text-slate-500 font-mono">
                  ID: {inspectDocId}
                </p>
              </div>
              <button onClick={closeInspector} className="p-1 rounded-lg hover:bg-slate-200 text-slate-500">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {loadingInspect ? (
                <div className="p-12 text-center text-slate-500">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto text-emerald-600 mb-2" />
                  Analyzing processed chunks...
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
      )}
    </div>
  );
};
