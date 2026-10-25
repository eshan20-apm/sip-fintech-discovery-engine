import React from 'react';
import { Search, Download, RefreshCw, Filter, Sparkles } from 'lucide-react';

export const THEMES = [
  "All",
  "Income timing",
  "Unnoticed failed autopay",
  "Expectation gap (Returns/Losses)",
  "Cancel instead of pause",
  "Platform UX / Glitch",
  "Charges & Taxes",
  "Switching Platform",
  "Other",
  "Unclear"
];

export const JOURNEY_STAGES = [
  "All",
  "Before starting / KYC",
  "First instalment",
  "Months 2 to 6",
  "Experienced / Multi-year",
  "Unclear"
];

export const ACTIONS = [
  "All",
  "Continued",
  "Paused",
  "Reduced",
  "Stopped",
  "Switched Platform",
  "Unsure",
  "Unclear"
];

export const WHO_CAN_FIX_IT = [
  "All",
  "Fintech Platform (Groww, Zerodha, etc.)",
  "Bank or AMC",
  "User's own life",
  "Regulator (SEBI/RBI)",
  "Unclear"
];

export const PLATFORMS = [
  "All",
  "Groww",
  "Zerodha",
  "AngelOne",
  "General MF"
];

export default function FilterBar({
  filters,
  onFilterChange,
  onSearchChange,
  onOpenFetchModal,
  onExportExcel,
  isExporting
}) {
  return (
    <div className="control-bar">
      <div className="search-row">
        <div className="search-input-wrapper">
          <Search className="search-icon" size={18} />
          <input
            type="text"
            className="search-input"
            placeholder="Search keywords in reviews or questions (e.g. 'mandate bounce', 'salary date', 'cancel SIP')..."
            value={filters.search_query}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>

        <button 
          className="btn-primary"
          onClick={onOpenFetchModal}
          title="Fetch live posts from Google Play Store & Reddit"
        >
          <RefreshCw size={16} />
          <span>Fetch Live Data</span>
        </button>

        <button 
          className="btn-secondary"
          onClick={onExportExcel}
          disabled={isExporting}
          title="Export active filtered view to Excel (.xlsx)"
        >
          <Download size={16} />
          <span>{isExporting ? 'Exporting...' : 'Download Excel'}</span>
        </button>
      </div>

      <div className="filters-row">
        {/* Platform Filter */}
        <div className="filter-group">
          <span className="filter-label">Platform:</span>
          <select 
            className="filter-select"
            value={filters.platform}
            onChange={(e) => onFilterChange('platform', e.target.value)}
          >
            {PLATFORMS.map(p => (
              <option key={p} value={p === 'All' ? 'all' : p}>{p}</option>
            ))}
          </select>
        </div>

        {/* Theme Filter */}
        <div className="filter-group">
          <span className="filter-label">Theme:</span>
          <select 
            className="filter-select"
            value={filters.theme}
            onChange={(e) => onFilterChange('theme', e.target.value)}
          >
            {THEMES.map(t => (
              <option key={t} value={t === 'All' ? 'all' : t}>{t}</option>
            ))}
          </select>
        </div>

        {/* Journey Stage Filter */}
        <div className="filter-group">
          <span className="filter-label">Stage:</span>
          <select 
            className="filter-select"
            value={filters.journey_stage}
            onChange={(e) => onFilterChange('journey_stage', e.target.value)}
          >
            {JOURNEY_STAGES.map(s => (
              <option key={s} value={s === 'All' ? 'all' : s}>{s}</option>
            ))}
          </select>
        </div>

        {/* Action Taken Filter */}
        <div className="filter-group">
          <span className="filter-label">Action:</span>
          <select 
            className="filter-select"
            value={filters.what_they_did}
            onChange={(e) => onFilterChange('what_they_did', e.target.value)}
          >
            {ACTIONS.map(a => (
              <option key={a} value={a === 'All' ? 'all' : a}>{a}</option>
            ))}
          </select>
        </div>

        {/* Who Can Fix It Filter */}
        <div className="filter-group">
          <span className="filter-label">Fixer:</span>
          <select 
            className="filter-select"
            value={filters.who_can_fix_it}
            onChange={(e) => onFilterChange('who_can_fix_it', e.target.value)}
          >
            {WHO_CAN_FIX_IT.map(f => (
              <option key={f} value={f === 'All' ? 'all' : f}>{f}</option>
            ))}
          </select>
        </div>

        {/* Verification Status Filter */}
        <div className="filter-group">
          <span className="filter-label">Status:</span>
          <select 
            className="filter-select"
            value={filters.status}
            onChange={(e) => onFilterChange('status', e.target.value)}
          >
            <option value="all">All Posts</option>
            <option value="hand_labelled">Hand-Labelled Golden Truth</option>
            <option value="ai_tagged">AI Tagged Only</option>
          </select>
        </div>
      </div>
    </div>
  );
}
