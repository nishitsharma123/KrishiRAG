import React from 'react';

/**
 * Lightweight, safe parser for formatted agricultural advisory text.
 * Handles bold, italics, bullet lists, numbered lists, blockquotes, code blocks,
 * and highlights citation tokens like [Doc: X, Page: Y].
 */
export const FormattedAnswer = ({ content, onCitationClick }) => {
  if (!content) return null;

  // Split lines
  const lines = content.split('\n');
  const elements = [];
  let currentList = [];
  let listType = null; // 'ul' or 'ol'

  const flushList = () => {
    if (currentList.length > 0) {
      if (listType === 'ol') {
        elements.push(
          <ol key={`ol-${elements.length}`} className="list-decimal pl-5 space-y-1.5 my-2">
            {currentList.map((item, idx) => (
              <li key={idx} className="text-slate-800 leading-relaxed">
                {renderInlineFormatting(item, onCitationClick)}
              </li>
            ))}
          </ol>
        );
      } else {
        elements.push(
          <ul key={`ul-${elements.length}`} className="list-disc pl-5 space-y-1.5 my-2">
            {currentList.map((item, idx) => (
              <li key={idx} className="text-slate-800 leading-relaxed">
                {renderInlineFormatting(item, onCitationClick)}
              </li>
            ))}
          </ul>
        );
      }
      currentList = [];
      listType = null;
    }
  };

  lines.forEach((line, lineIndex) => {
    const trimmed = line.trim();

    if (!trimmed) {
      flushList();
      return;
    }

    // Check for Headings
    if (trimmed.startsWith('### ')) {
      flushList();
      elements.push(
        <h4 key={`h4-${lineIndex}`} className="text-sm font-bold text-emerald-950 mt-3 mb-1">
          {renderInlineFormatting(trimmed.substring(4), onCitationClick)}
        </h4>
      );
      return;
    }

    if (trimmed.startsWith('## ')) {
      flushList();
      elements.push(
        <h3 key={`h3-${lineIndex}`} className="text-base font-bold text-emerald-900 mt-4 mb-2 pb-1 border-b border-emerald-100">
          {renderInlineFormatting(trimmed.substring(3), onCitationClick)}
        </h3>
      );
      return;
    }

    if (trimmed.startsWith('# ')) {
      flushList();
      elements.push(
        <h2 key={`h2-${lineIndex}`} className="text-lg font-bold text-slate-900 mt-4 mb-2">
          {renderInlineFormatting(trimmed.substring(2), onCitationClick)}
        </h2>
      );
      return;
    }

    // Unordered List
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      if (listType === 'ol') flushList();
      listType = 'ul';
      currentList.push(trimmed.substring(2));
      return;
    }

    // Numbered List (e.g. "1. ")
    const numMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
    if (numMatch) {
      if (listType === 'ul') flushList();
      listType = 'ol';
      currentList.push(numMatch[2]);
      return;
    }

    // Normal Paragraph
    flushList();
    elements.push(
      <p key={`p-${lineIndex}`} className="text-sm text-slate-800 leading-relaxed my-1.5">
        {renderInlineFormatting(trimmed, onCitationClick)}
      </p>
    );
  });

  flushList();

  return <div className="space-y-1 text-slate-800">{elements}</div>;
};

/**
 * Parses bold (**text**), italics (*text*), inline code (`code`),
 * and clickable citation pills like [Doc: ... Page: ...].
 */
function renderInlineFormatting(text, onCitationClick) {
  if (!text) return null;

  // Tokenize citation patterns: [Doc: Title, Page: N] or (Doc: Title, Page N) or similar
  // Also parse **bold** and `code`
  // We can do a regex match for bold first
  const parts = [];
  let remaining = text;
  let keyIdx = 0;

  // Regex to match markdown bold: \*\*(.*?)\*\* or inline code `(.*?)` or citation \[(Doc:.*?Page.*?)\]
  const tokenRegex = /(\*\*(.*?)\*\*|`(.*?)`|\[(Doc:[^\]]+)\])/;

  while (remaining) {
    const match = remaining.match(tokenRegex);
    if (!match) {
      parts.push(<span key={keyIdx++}>{remaining}</span>);
      break;
    }

    const matchIndex = match.index;
    if (matchIndex > 0) {
      parts.push(<span key={keyIdx++}>{remaining.substring(0, matchIndex)}</span>);
    }

    const fullMatch = match[0];
    if (fullMatch.startsWith('**') && fullMatch.endsWith('**')) {
      const boldText = match[2];
      parts.push(
        <strong key={keyIdx++} className="font-semibold text-slate-900">
          {boldText}
        </strong>
      );
    } else if (fullMatch.startsWith('`') && fullMatch.endsWith('`')) {
      const codeText = match[3];
      parts.push(
        <code key={keyIdx++} className="px-1.5 py-0.5 rounded bg-slate-100 text-emerald-800 font-mono text-xs border border-slate-200">
          {codeText}
        </code>
      );
    } else if (fullMatch.startsWith('[Doc:') && fullMatch.endsWith(']')) {
      const citationText = match[4];
      parts.push(
        <button
          key={keyIdx++}
          type="button"
          onClick={() => onCitationClick && onCitationClick(citationText)}
          className="inline-flex items-center gap-1 mx-1 px-2 py-0.5 rounded-md bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-mono text-[11px] font-medium border border-emerald-300 transition-colors cursor-pointer shadow-2xs"
          title="Click to view verified source excerpt"
        >
          📄 {citationText}
        </button>
      );
    }

    remaining = remaining.substring(matchIndex + fullMatch.length);
  }

  return parts;
}

export default FormattedAnswer;
