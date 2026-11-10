import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  ShieldCheck, 
  FileText, 
  AlertTriangle,
  RefreshCw,
  PlusCircle,
  Clock,
  CheckCircle2,
  Filter,
  Layers,
  ChevronRight,
  ExternalLink,
  ShieldAlert
} from 'lucide-react';
import { apiService } from '../services/api';
import { useApp } from '../context/AppContext';
import { FormattedAnswer } from '../components/FormattedAnswer';
import { CitationSidecar } from '../components/CitationSidecar';

const CROP_OPTIONS = [
  { label: 'All Crops', value: '' },
  { label: 'Wheat (गेहूं)', value: 'wheat' },
  { label: 'Paddy / Rice (धान)', value: 'paddy' },
  { label: 'Mustard (सरसों)', value: 'mustard' },
  { label: 'Sugarcane (गन्ना)', value: 'sugarcane' },
  { label: 'Cotton (कपास)', value: 'cotton' },
  { label: 'Gram / Chickpea (चना)', value: 'chickpea' },
];

const SUGGESTED_QUERIES = [
  {
    query: 'What is the recommended seed rate for timely sown wheat in NWPZ?',
    crop: 'wheat',
    category: 'Agronomy / Seed Rate'
  },
  {
    query: 'How to identify and manage Yellow Rust in Wheat according to ICAR?',
    crop: 'wheat',
    category: 'Disease Management'
  },
  {
    query: 'What are the critical irrigation stages for wheat crop?',
    crop: 'wheat',
    category: 'Water Management'
  },
  {
    query: 'What is the recommended NPK fertilizer schedule for irrigated wheat?',
    crop: 'wheat',
    category: 'Nutrient Management'
  },
  {
    query: 'How to cultivate dragon fruit in Antarctica sub-zero soil?',
    crop: '',
    category: 'Abstention Test (Out of Scope)'
  }
];

export const ChatPage = () => {
  const { llmStatus, loadingLLM } = useApp();

  // Multi-turn session persistence
  const [sessionId, setSessionId] = useState(() => {
    const existing = localStorage.getItem('krishirag_session_id');
    if (existing) return existing;
    const newId = 'session_' + Math.random().toString(36).substring(2, 10);
    localStorage.setItem('krishirag_session_id', newId);
    return newId;
  });

  const [messages, setMessages] = useState([
    {
      id: 'welcome-init',
      role: 'assistant',
      content: `Namaste! I am **KrishiRAG**, your verified agricultural advisory system.\n\nI answer queries strictly grounded in official publications from the **Indian Council of Agricultural Research (ICAR)** and State Agricultural Universities. Every agronomic recommendation, seed rate, and fertilizer dosage is cross-checked against indexed documents with verifiable page citations.\n\nSelect a verified crop topic below or type your farming query to begin.`,
      sources: [],
      retrieved_chunks: [],
      abstained: false,
      retrieval_time_ms: 0,
      generation_time_ms: 0,
    }
  ]);

  const [inputQuery, setInputQuery] = useState('');
  const [selectedCrop, setSelectedCrop] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState('');
  const [errorMessage, setErrorMessage] = useState(null);

  // Citation Sidecar State
  const [sidecarOpen, setSidecarOpen] = useState(false);
  const [sidecarMessage, setSidecarMessage] = useState(null);
  const [sidecarCitationIdx, setSidecarCitationIdx] = useState(0);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load conversation history on mount
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const historyData = await apiService.getChatHistory(sessionId);
        if (historyData?.messages && historyData.messages.length > 0) {
          const loaded = historyData.messages.map((m, idx) => ({
            id: `hist_${m.id || idx}`,
            role: m.role,
            content: m.content,
            sources: [],
            retrieved_chunks: [],
            abstained: m.content.toLowerCase().includes('insufficient') && m.role === 'assistant',
            created_at: m.created_at,
          }));
          setMessages(loaded);
        }
      } catch (err) {
        // Non-blocking: keep local state
        console.warn('Could not restore chat history for session:', sessionId, err);
      }
    };

    fetchHistory();
  }, [sessionId]);

  const startNewSession = () => {
    const freshId = 'session_' + Math.random().toString(36).substring(2, 10);
    localStorage.setItem('krishirag_session_id', freshId);
    setSessionId(freshId);
    setMessages([
      {
        id: 'welcome-reset',
        role: 'assistant',
        content: `**New Advisory Session Initialized**\n\nAsk any question regarding crop varieties, sowing windows, fertilizer schedules, or disease management verified by ICAR.`,
        sources: [],
        retrieved_chunks: [],
        abstained: false,
      }
    ]);
    setErrorMessage(null);
  };

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    const query = inputQuery.trim();
    if (!query || loading) return;

    setErrorMessage(null);
    setInputQuery('');

    // Append user message
    const userMsg = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: query,
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setLoadingStage('Hybrid dense vector (multilingual-e5) + BM25 keyword search...');

    // Progress updates for UX
    const stageTimer1 = setTimeout(() => {
      setLoadingStage('Reranking top candidates with Cross-Encoder (ms-marco-MiniLM)...');
    }, 1800);

    const stageTimer2 = setTimeout(() => {
      setLoadingStage('Qwen3:4b local reasoning & evidence-grounded generation...');
    }, 3800);

    try {
      const filters = {};
      if (selectedCrop) filters.crop = selectedCrop;

      const res = await apiService.askChat({
        session_id: sessionId,
        question: query,
        filters: Object.keys(filters).length > 0 ? filters : undefined,
      });

      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);

      const assistantMsg = {
        id: `asst_${Date.now()}`,
        role: 'assistant',
        content: res.answer,
        sources: res.sources || [],
        retrieved_chunks: res.retrieved_chunks || [],
        abstained: res.abstained || false,
        abstention_reason: res.abstention_reason,
        retrieval_time_ms: res.retrieval_time_ms,
        generation_time_ms: res.generation_time_ms,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      setErrorMessage(
        err.message || 'Failed to complete RAG inference. Please verify that Ollama is running.'
      );
    } finally {
      setLoading(false);
      setLoadingStage('');
    }
  };

  const handleSelectSuggested = (item) => {
    setInputQuery(item.query);
    if (item.crop) setSelectedCrop(item.crop);
  };

  const openSidecarForMessage = (msg, citationIdx = 0) => {
    setSidecarMessage(msg);
    setSidecarCitationIdx(citationIdx);
    setSidecarOpen(true);
  };

  return (
    <div className="h-[calc(100vh-7.5rem)] flex flex-col bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
      {/* Top Advisory Control Bar */}
      <div className="px-6 py-3 border-b border-slate-200/80 bg-slate-50/70 flex flex-wrap items-center justify-between gap-3">
        {/* Left: Active session & mode */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-bold text-slate-800">
              Verified Advisory Session
            </span>
          </div>
          <span className="text-slate-300">|</span>
          <div className="text-[11px] font-mono text-slate-500">
            ID: {sessionId.substring(0, 14)}...
          </div>
        </div>

        {/* Right: Filter & New Session Button */}
        <div className="flex items-center gap-2.5">
          {/* Crop Filter Selector */}
          <div className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-lg border border-slate-200 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-500 font-medium">Crop:</span>
            <select
              value={selectedCrop}
              onChange={(e) => setSelectedCrop(e.target.value)}
              className="bg-transparent font-semibold text-slate-800 focus:outline-none text-xs cursor-pointer"
            >
              {CROP_OPTIONS.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          {/* New Session Button */}
          <button
            onClick={startNewSession}
            title="Start fresh conversation session"
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white border border-slate-200 hover:bg-slate-100 text-xs font-semibold text-slate-700 transition-colors shadow-2xs"
          >
            <PlusCircle className="w-3.5 h-3.5 text-emerald-600" />
            <span>New Chat</span>
          </button>
        </div>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-9 h-9 rounded-xl bg-emerald-700 text-white flex items-center justify-center shrink-0 shadow-xs mt-1">
                <Bot className="w-5 h-5" />
              </div>
            )}

            <div
              className={`max-w-3xl rounded-2xl p-5 text-sm leading-relaxed transition-all ${
                msg.role === 'user'
                  ? 'bg-emerald-700 text-white rounded-tr-none shadow-xs'
                  : 'bg-white border border-slate-200/90 text-slate-800 rounded-tl-none shadow-xs'
              }`}
            >
              {/* Abstention Warning Banner if triggered */}
              {msg.role === 'assistant' && msg.abstained && (
                <div className="mb-4 p-3.5 bg-amber-50/90 border border-amber-200 rounded-xl flex items-start gap-2.5 text-amber-900 text-xs">
                  <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold block">
                      Strict Abstention Policy Triggered
                    </span>
                    <span className="text-amber-800">
                      Zero-hallucination constraint active. The indexed ICAR publications do not contain sufficient evidence to formulate verified advice for this query.
                    </span>
                    {msg.abstention_reason && (
                      <span className="block mt-1 font-mono text-[10px] text-amber-700">
                        Reason: {msg.abstention_reason}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Message Content */}
              {msg.role === 'user' ? (
                <div className="font-medium whitespace-pre-wrap">{msg.content}</div>
              ) : (
                <FormattedAnswer
                  content={msg.content}
                  onCitationClick={() => openSidecarForMessage(msg)}
                />
              )}

              {/* Verified Sources & Timing Footnote for Assistant */}
              {msg.role === 'assistant' && (
                <div className="mt-4 pt-3.5 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
                  {/* Sources pill button */}
                  {msg.sources && msg.sources.length > 0 ? (
                    <button
                      onClick={() => openSidecarForMessage(msg, 0)}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-50 hover:bg-emerald-100/80 border border-emerald-200 text-emerald-800 font-semibold transition-colors"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>{msg.sources.length} Verified Sources</span>
                      <ChevronRight className="w-3 h-3 text-emerald-500" />
                    </button>
                  ) : (
                    <span className="text-[11px] text-slate-400">
                      {msg.abstained ? 'No Grounding Chunks' : 'ICAR General Advisory'}
                    </span>
                  )}

                  {/* Latency Metrics */}
                  {(msg.retrieval_time_ms > 0 || msg.generation_time_ms > 0) && (
                    <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
                      <Clock className="w-3 h-3" />
                      <span>
                        Retrieval: {(msg.retrieval_time_ms / 1000).toFixed(2)}s
                      </span>
                      <span>•</span>
                      <span>
                        Gen: {(msg.generation_time_ms / 1000).toFixed(1)}s
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-9 h-9 rounded-xl bg-slate-800 text-white flex items-center justify-center shrink-0 shadow-xs mt-1">
                <User className="w-5 h-5" />
              </div>
            )}
          </div>
        ))}

        {/* Loading Pulse State */}
        {loading && (
          <div className="flex gap-3.5 justify-start">
            <div className="w-9 h-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center shrink-0 animate-pulse">
              <Bot className="w-5 h-5" />
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 max-w-lg space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-emerald-800">
                <RefreshCw className="w-4 h-4 animate-spin text-emerald-600" />
                <span>Agricultural Grounding Pipeline Active</span>
              </div>
              <p className="text-xs text-slate-600 font-mono animate-pulse">
                {loadingStage}
              </p>
              <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 animate-[pulse_1.5s_ease-in-out_infinite]" />
              </div>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {errorMessage && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-xs font-semibold text-rose-700 underline hover:text-rose-900"
            >
              Dismiss
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts Banner (visible if conversation is short) */}
      {messages.length <= 2 && (
        <div className="px-6 py-2.5 bg-slate-50/80 border-t border-slate-200/80">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-2 font-medium">
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>Sample Verified ICAR Questions:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUERIES.map((item, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectSuggested(item)}
                className="text-xs bg-white hover:bg-emerald-50 text-slate-700 hover:text-emerald-800 px-3 py-1.5 rounded-lg border border-slate-200 transition-colors text-left flex items-center gap-1.5 shadow-2xs"
              >
                <span>{item.query}</span>
                <span className="text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                  {item.category}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Question Input Form */}
      <form onSubmit={handleSend} className="p-4 border-t border-slate-200 bg-white flex gap-3">
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          disabled={loading}
          placeholder="Ask an agricultural question (e.g. Yellow Rust management, wheat seed rate, NPK dose)..."
          className="flex-1 px-4 py-3 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 transition-all placeholder:text-slate-400 disabled:bg-slate-50"
        />
        <button
          type="submit"
          disabled={!inputQuery.trim() || loading}
          className="px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white font-semibold text-sm transition-colors flex items-center gap-2 shadow-xs shrink-0 cursor-pointer disabled:cursor-not-allowed"
        >
          {loading ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
          <span>{loading ? 'Reasoning...' : 'Ask Advisory'}</span>
        </button>
      </form>

      {/* Interactive Citation Sidecar Drawer */}
      <CitationSidecar
        isOpen={sidecarOpen}
        onClose={() => setSidecarOpen(false)}
        activeMessage={sidecarMessage}
        selectedCitationIndex={sidecarCitationIdx}
      />
    </div>
  );
};

export default ChatPage;
