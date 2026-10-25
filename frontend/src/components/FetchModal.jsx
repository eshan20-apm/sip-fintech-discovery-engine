import React, { useState } from 'react';
import { X, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';

export default function FetchModal({ isOpen, onClose, onFetchComplete }) {
  if (!isOpen) return null;

  const [query, setQuery] = useState('SIP autopay failed OR mandate bounce OR cancel SIP');
  const [platforms, setPlatforms] = useState(['Groww', 'Zerodha', 'AngelOne']);
  const [sources, setSources] = useState(['playstore', 'reddit']);
  const [limit, setLimit] = useState(20);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const togglePlatform = (p) => {
    setPlatforms(prev => 
      prev.includes(p) ? prev.filter(item => item !== p) : [...prev, p]
    );
  };

  const toggleSource = (s) => {
    setSources(prev => 
      prev.includes(s) ? prev.filter(item => item !== s) : [...prev, s]
    );
  };

  const handleFetch = async () => {
    if (platforms.length === 0 || sources.length === 0) {
      setError('Please select at least one platform and one source');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const resp = await fetch('/api/fetch-live', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          platforms,
          sources,
          limit_per_source: Number(limit)
        })
      });

      if (!resp.ok) {
        throw new Error(`Server returned ${resp.status}`);
      }

      const data = await resp.json();
      setResult(data);
      if (onFetchComplete) {
        onFetchComplete();
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch live data');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <RefreshCw size={18} style={{ color: '#818cf8' }} />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
              Fetch Free Live Data
            </h3>
          </div>
          <button onClick={onClose} className="btn-close">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {error && (
            <div style={{ padding: '10px 14px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '6px', color: '#fca5a5', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {result && (
            <div style={{ padding: '12px 16px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '6px', color: '#6ee7b7', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={18} />
              <span>
                Successfully ingested <strong>{result.total_fetched}</strong> posts ({result.saved_count} new records enriched & saved)!
              </span>
            </div>
          )}

          <div className="field-group">
            <label className="field-label">Target Friction Search Terms</label>
            <input 
              type="text" 
              className="field-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. SIP mandate failed OR bounce charges"
              disabled={isLoading}
            />
          </div>

          <div className="field-group">
            <label className="field-label">Target Investment Apps</label>
            <div className="checkbox-row">
              {['Groww', 'Zerodha', 'AngelOne'].map(p => (
                <label key={p} className="checkbox-label">
                  <input 
                    type="checkbox"
                    checked={platforms.includes(p)}
                    onChange={() => togglePlatform(p)}
                    disabled={isLoading}
                  />
                  <span>{p === 'Zerodha' ? 'Zerodha Coin' : p === 'AngelOne' ? 'Angel One' : p}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="field-group">
            <label className="field-label">Free Public Sources</label>
            <div className="checkbox-row">
              <label className="checkbox-label">
                <input 
                  type="checkbox"
                  checked={sources.includes('playstore')}
                  onChange={() => toggleSource('playstore')}
                  disabled={isLoading}
                />
                <span>Google Play Store (Reviews)</span>
              </label>
              <label className="checkbox-label">
                <input 
                  type="checkbox"
                  checked={sources.includes('reddit')}
                  onChange={() => toggleSource('reddit')}
                  disabled={isLoading}
                />
                <span>Reddit (Discussions)</span>
              </label>
            </div>
          </div>

          <div className="field-group">
            <label className="field-label">Fetch Depth Per Source</label>
            <select 
              className="field-select"
              value={limit}
              onChange={(e) => setLimit(e.target.value)}
              disabled={isLoading}
            >
              <option value="10">10 reviews per app (Quick ~5s)</option>
              <option value="20">20 reviews per app (Balanced ~10s)</option>
              <option value="30">30 reviews per app (Deep ~15s)</option>
              <option value="50">50 reviews per app (Comprehensive)</option>
            </select>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose} disabled={isLoading}>
            Close
          </button>
          <button 
            className="btn-primary" 
            onClick={handleFetch} 
            disabled={isLoading}
          >
            <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
            <span>{isLoading ? 'Fetching & Tagging...' : 'Start Live Ingestion'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
