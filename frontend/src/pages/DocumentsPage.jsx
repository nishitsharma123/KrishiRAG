import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  UploadCloud, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Building2, 
  Calendar,
  Layers,
  RefreshCw
} from 'lucide-react';
import { apiService } from '../services/api';

export const DocumentsPage = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

      {/* Upload Dropzone (Phase 2 Ingestion Hub) */}
      <div className="p-8 rounded-2xl border-2 border-dashed border-slate-200 bg-white hover:border-emerald-500/60 transition-colors text-center space-y-3 cursor-pointer group">
        <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto group-hover:scale-105 transition-transform shadow-xs">
          <UploadCloud className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <p className="text-sm font-bold text-slate-800">
            Upload Official ICAR PDF Bulletins & Guides
          </p>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Drag and drop packages of practices, SAU crop advisories, or bulletins. 
            Automated text extraction and page preservation will execute during Phase 2.
          </p>
        </div>
        <div className="inline-flex items-center gap-2 text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
          Supported Format: PDF (Up to 100MB)
        </div>
      </div>

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
            <p className="text-sm font-semibold text-slate-700">No ICAR Documents Ingested Yet</p>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Phase 1 foundation verified. Documents will be populated in Phase 2 using PyMuPDF page-bound extraction.
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
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Registered At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-3.5 font-medium text-slate-900 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span>{doc.title}</span>
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
                    <td className="px-6 py-3.5">
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                        <CheckCircle className="w-3 h-3" />
                        {doc.status}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-slate-500 font-mono">
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
