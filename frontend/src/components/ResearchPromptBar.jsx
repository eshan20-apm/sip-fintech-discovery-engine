import React, { useState } from 'react';
import { Sparkles, ArrowRight, Download, RefreshCw, Layers } from 'lucide-react';

const SUGGESTED_QUERIES = [
  "Why do beginners cancel SIPs during market downturns?",
  "What issues occur with SIP date vs salary credit date?",
  "Why do users cancel instead of pausing their SIP?",
  "What friction happens when switching from Groww to Zerodha Coin?",
  "Why do HDFC or SBI bank autopay mandates fail on Zerodha Coin?"
];

export default function ResearchPromptBar({
  onRunResearch,
  isLoading,
  platform,
  onPlatformChange,
  status,
  onStatusChange,
  onExportExcel,
  isExporting,
  queryAnalysis
}) {
  const [inputQuery, setInputQuery] = useState('');

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (inputQuery.trim() && !isLoading) {
      onRunResearch(inputQuery.trim());
    }
  };

  const handleChipClick = (suggestion) => {
    setInputQuery(suggestion);
    onRunResearch(suggestion);
  };

  return (
    <div className="prompt-workbench-card">
      {/* Central Conversational Prompt Box (ChatGPT / Gemini style) */}
      <form onSubmit={handleSubmit} className="prompt-form">
        <div className="prompt-input-container">
          <div className="prompt-icon-wrapper">
            <Sparkles size={20} className={isLoading ? "text-indigo-400 animate-spin" : "text-indigo-400"} />
          </div>
          <input
            type="text"
            className="prompt-input"
            placeholder="Ask any research question about SIP investor behavior (e.g. 'Why do beginners stop SIPs in market drops?', 'Why switch from Groww to Coin?')..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isLoading}
          />
          <button 
            type="submit" 
            className="btn-prompt-submit"
            disabled={!inputQuery.trim() || isLoading}
            title="Ask AI to analyze query, ingest live data & tag investor behavior"
          >
            <span>{isLoading ? 'Researching...' : 'Research'}</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </form>

      {/* Suggested Research Prompts */}
      <div className="prompt-suggestions-row">
        <span className="suggestion-label">Suggested research:</span>
        <div className="chips-wrapper">
          {SUGGESTED_QUERIES.map((suggestion, idx) => (
            <button
              key={idx}
              type="button"
              className="chip-suggestion"
              onClick={() => handleChipClick(suggestion)}
              disabled={isLoading}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      {/* Active Query Analysis Banner (if researcher ran a prompt) */}
      {queryAnalysis && (
        <div className="query-analysis-banner">
          <div className="analysis-indicator">
            <span className="pulse-dot"></span>
            <strong>LLM Query Intent:</strong> {queryAnalysis.intent_summary || "Analyzing investor feedback"}
          </div>
          <div className="analysis-tags">
            {queryAnalysis.search_keywords?.slice(0, 3).map((kw, idx) => (
              <span key={idx} className="analysis-tag-badge">🔍 {kw}</span>
            ))}
          </div>
        </div>
      )}

      {/* Secondary Bar: Platform Scope & Excel Export (No rigid dropdown filters!) */}
      <div className="prompt-controls-subbar">
        <div className="platform-filter-pills">
          <span className="filter-pill-label">Platform Scope:</span>
          {['all', 'Groww', 'Zerodha', 'AngelOne', 'INDmoney', 'PaytmMoney'].map((p) => (
            <button
              key={p}
              type="button"
              className={`filter-pill ${platform === p ? 'active' : ''}`}
              onClick={() => onPlatformChange(p)}
            >
              {p === 'all' ? 'All Apps' : p === 'Zerodha' ? 'Zerodha Coin' : p === 'AngelOne' ? 'Angel One' : p === 'PaytmMoney' ? 'Paytm Money' : p}
            </button>
          ))}

          <span className="filter-pill-label" style={{ marginLeft: '12px' }}>Status:</span>
          {[
            { id: 'all', label: 'All Posts' },
            { id: 'hand_labelled', label: 'Golden Benchmark' },
            { id: 'ai_tagged', label: 'AI Tagged' }
          ].map((s) => (
            <button
              key={s.id}
              type="button"
              className={`filter-pill ${status === s.id ? 'active' : ''}`}
              onClick={() => onStatusChange(s.id)}
            >
              {s.label}
            </button>
          ))}
        </div>

        <button 
          type="button"
          className="btn-secondary"
          onClick={onExportExcel}
          disabled={isExporting}
          title="Export current research view to Excel (.xlsx)"
        >
          <Download size={15} />
          <span>{isExporting ? 'Exporting...' : 'Download Excel'}</span>
        </button>
      </div>
    </div>
  );
}
