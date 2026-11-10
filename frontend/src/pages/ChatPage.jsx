import React, { useState } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  ShieldCheck, 
  FileText, 
  AlertCircle,
  HelpCircle
} from 'lucide-react';
import { useApp } from '../context/AppContext';

export const ChatPage = () => {
  const { health } = useApp();
  const [inputQuery, setInputQuery] = useState('');
  const [messages, setMessages] = useState([
    {
      id: 'welcome-msg',
      role: 'assistant',
      content: 'Namaste! I am KrishiRAG, your verified agricultural advisor. I provide crop management, fertilizer dosage, and pest control recommendations strictly derived from authentic ICAR publications with verifiable citations.\n\nHow may I assist your farm today?',
      citations: []
    }
  ]);

  const samplePrompts = [
    'What is the recommended seed rate for Timely Sown Irrigated Wheat in NWPZ?',
    'How do I manage Yellow Rust in Wheat according to ICAR guidelines?',
    'What is the balanced NPK fertilizer schedule for Kharif Paddy in Punjab?',
    'Which biocontrol agents are approved for Stem Borer in sugarcane?'
  ];

  const handleSelectPrompt = (prompt) => {
    setInputQuery(prompt);
  };

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputQuery.trim()) return;

    const userMsg = {
      id: String(Date.now()),
      role: 'user',
      content: inputQuery.trim(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');

    // Phase 1 preview response: informs user that RAG pipeline unlocks in Phase 4
    setTimeout(() => {
      const assistantMsg = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: `**Query Registered**: "${userMsg.content}"\n\n*Phase 1 Foundation Status*: The backend foundation and SQLite database are active. The hybrid vector retrieval pipeline, ICAR document ingestion (Phase 2 & 3), and Qwen3 LLM reasoning (Phase 4) will execute this query against authentic publications in upcoming phases.`,
        citations: []
      };
      setMessages((prev) => [...prev, assistantMsg]);
    }, 400);
  };

  return (
    <div className="h-[calc(100vh-8.5rem)] flex flex-col bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      {/* Chat Sub-Header */}
      <div className="px-6 py-3.5 border-b border-slate-100 bg-slate-50/70 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-bold text-slate-800">
            Agricultural Advisory Session
          </span>
          <span className="text-[11px] text-slate-500 font-medium hidden sm:inline">
            (Ground-Truth Verifiable Mode)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-medium text-emerald-800 bg-emerald-100/75 px-2.5 py-0.5 rounded-full border border-emerald-200">
            Qwen3 4B Grounded Prompting
          </span>
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
              <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-xs">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-2xl rounded-2xl p-4 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-emerald-700 text-white rounded-tr-none shadow-xs'
                  : 'bg-slate-50 border border-slate-200/80 text-slate-800 rounded-tl-none'
              }`}
            >
              <div className="whitespace-pre-line">{msg.content}</div>

              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-200 space-y-1.5">
                  <span className="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
                    <FileText className="w-3 h-3 text-emerald-600" />
                    Verified ICAR Sources:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {msg.citations.map((c, i) => (
                      <span
                        key={i}
                        className="text-[10px] font-mono bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-700"
                      >
                        {c.doc} (Page {c.page})
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-slate-800 text-white flex items-center justify-center shrink-0">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Query Suggestions (If first interaction) */}
      {messages.length === 1 && (
        <div className="px-6 py-2 bg-slate-50/50 border-t border-slate-100">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-2 font-medium">
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>Suggested ICAR Practice Queries:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {samplePrompts.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectPrompt(p)}
                className="text-xs bg-white hover:bg-emerald-50 text-slate-700 hover:text-emerald-800 px-3 py-1.5 rounded-lg border border-slate-200 transition-colors text-left"
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Message Form */}
      <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-200 bg-white flex gap-3">
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder="Ask an agricultural question (e.g. Yellow rust management, fertilizer dosages, seed rate)..."
          className="flex-1 px-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 transition-all placeholder:text-slate-400"
        />
        <button
          type="submit"
          disabled={!inputQuery.trim()}
          className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white font-semibold text-sm transition-colors flex items-center gap-2 shadow-xs"
        >
          <span>Ask</span>
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
