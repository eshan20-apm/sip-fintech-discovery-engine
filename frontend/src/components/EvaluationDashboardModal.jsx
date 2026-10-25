import React, { useState, useEffect } from 'react';
import { 
  X, 
  ShieldCheck, 
  Activity, 
  Grid3X3, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight, 
  Sparkles, 
  Check, 
  Layers,
  HelpCircle,
  ExternalLink
} from 'lucide-react';

export default function EvaluationDashboardModal({ isOpen, onClose, onRefreshData }) {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'matrix', 'disagreements'
  const [metrics, setMetrics] = useState(null);
  const [matrixData, setMatrixData] = useState(null);
  const [matrixField, setMatrixField] = useState('theme');
  const [disagreements, setDisagreements] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [resolvingId, setResolvingId] = useState(null);
  const [resolveSuccessMsg, setResolveSuccessMsg] = useState('');

  const fetchMetrics = async () => {
    try {
      const resp = await fetch('/api/evaluation/metrics');
      if (resp.ok) {
        const data = await resp.json();
        setMetrics(data);
      }
    } catch (err) {
      console.error('Failed to load evaluation metrics:', err);
    }
  };

  const fetchMatrix = async (field = matrixField) => {
    try {
      const resp = await fetch(`/api/evaluation/confusion-matrix?field=${field}`);
      if (resp.ok) {
        const data = await resp.json();
        setMatrixData(data);
      }
    } catch (err) {
      console.error('Failed to load confusion matrix:', err);
    }
  };

  const fetchDisagreements = async () => {
    try {
      const resp = await fetch('/api/evaluation/disagreements?limit=50');
      if (resp.ok) {
        const data = await resp.json();
        setDisagreements(data.disagreements || []);
      }
    } catch (err) {
      console.error('Failed to load disagreements:', err);
    }
  };

  useEffect(() => {
    if (isOpen) {
      setIsLoading(true);
      Promise.all([fetchMetrics(), fetchMatrix('theme'), fetchDisagreements()])
        .finally(() => setIsLoading(false));
    }
  }, [isOpen]);

  const handleFieldChange = (newField) => {
    setMatrixField(newField);
    fetchMatrix(newField);
  };

  const handleResolve = async (postId, resolutionType) => {
    setResolvingId(postId);
    try {
      const resp = await fetch('/api/evaluation/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ post_id: postId, resolution_type: resolutionType })
      });
      if (resp.ok) {
        setResolveSuccessMsg(resolutionType === 'accept_ai' ? 'Accepted AI Tag' : 'Kept Golden Truth');
        setTimeout(() => setResolveSuccessMsg(''), 2500);
        await Promise.all([fetchMetrics(), fetchDisagreements(), fetchMatrix()]);
        if (onRefreshData) onRefreshData();
      }
    } catch (err) {
      console.error('Resolution error:', err);
    } finally {
      setResolvingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="eval-modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="eval-modal-header">
          <div className="eval-modal-title-group">
            <div className="eval-title-row">
              <ShieldCheck size={22} className="text-emerald-400" />
              <h2>Golden Benchmark & AI Reliability Analytics</h2>
              {metrics && (
                <span className="kappa-pill-badge">
                  κ = {metrics.overall_kappa} ({metrics.interpretation})
                </span>
              )}
            </div>
            <p className="eval-subtitle">
              Chance-adjusted agreement (Cohen's Kappa κ) and classification error analysis comparing AI tagging against verified Golden Benchmarks.
            </p>
          </div>
          <button onClick={onClose} className="btn-close" title="Close (Esc)">
            <X size={20} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="eval-tabs-bar">
          <button 
            type="button" 
            className={`eval-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <Activity size={16} />
            <span>Cohen's Kappa & Reliability</span>
          </button>
          <button 
            type="button" 
            className={`eval-tab-btn ${activeTab === 'matrix' ? 'active' : ''}`}
            onClick={() => setActiveTab('matrix')}
          >
            <Grid3X3 size={16} />
            <span>Theme Confusion Matrix</span>
          </button>
          <button 
            type="button" 
            className={`eval-tab-btn ${activeTab === 'disagreements' ? 'active' : ''}`}
            onClick={() => setActiveTab('disagreements')}
          >
            <AlertTriangle size={16} />
            <span>Disagreement Inspector ({disagreements.length})</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="eval-modal-body">
          {resolveSuccessMsg && (
            <div className="eval-toast-banner">
              <CheckCircle2 size={16} />
              <span>{resolveSuccessMsg} — Benchmark updated!</span>
            </div>
          )}

          {/* TAB 1: OVERVIEW & COHEN'S KAPPA */}
          {activeTab === 'overview' && (
            <div className="eval-tab-content">
              {metrics ? (
                <>
                  <div className="eval-metrics-grid">
                    {/* Kappa Gauge Card */}
                    <div className="eval-card eval-gauge-card">
                      <div className="gauge-header">
                        <span className="card-label">Overall Chance-Adjusted Agreement</span>
                        <HelpCircle size={14} title="Cohen's Kappa measures agreement above random chance: 0.61-0.80 is Substantial, 0.81-1.00 is Almost Perfect." />
                      </div>
                      <div className="gauge-number-wrap">
                        <span className="gauge-big-num">
                          {metrics.overall_kappa >= 0 ? `+${metrics.overall_kappa}` : metrics.overall_kappa}
                        </span>
                        <span className="gauge-scale">/ 1.000 κ</span>
                      </div>
                      <div className="gauge-badge-row">
                        <span className="badge badge-golden">
                          {metrics.interpretation}
                        </span>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          {metrics.total_benchmarked} verified posts
                        </span>
                      </div>
                    </div>

                    {/* Overall Raw Agreement */}
                    <div className="eval-card">
                      <span className="card-label">Observed Raw Agreement (Pₒ)</span>
                      <div className="gauge-number-wrap">
                        <span className="gauge-big-num" style={{ color: '#10b981' }}>
                          {metrics.overall_agreement_rate}%
                        </span>
                      </div>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
                        Percentage of exact label agreements across all 4 behavioral classification fields.
                      </p>
                    </div>

                    {/* Field Breakdown Bars */}
                    <div className="eval-card eval-card-wide">
                      <span className="card-label">Field-Level Agreement & Reliability Breakdown</span>
                      <div className="field-breakdown-list">
                        {[
                          { key: 'theme', label: 'Dynamic Theme (2-3 Words)', data: metrics.fields?.theme },
                          { key: 'journey_stage', label: 'Journey Stage', data: metrics.fields?.journey_stage },
                          { key: 'what_they_did', label: 'Action Taken', data: metrics.fields?.what_they_did },
                          { key: 'who_can_fix_it', label: 'Who Can Fix It', data: metrics.fields?.who_can_fix_it }
                        ].map((f) => (
                          <div key={f.key} className="field-breakdown-row">
                            <div className="field-row-header">
                              <span className="field-name">{f.label}</span>
                              <div className="field-scores">
                                <span className="score-kappa">κ = {f.data?.kappa ?? 0}</span>
                                <span className="score-acc">{f.data?.accuracy ?? 0}% match</span>
                              </div>
                            </div>
                            <div className="progress-bar-track">
                              <div 
                                className="progress-bar-fill" 
                                style={{ width: `${Math.min(100, Math.max(5, f.data?.accuracy || 0))}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Benchmark Methodology Card */}
                  <div className="methodology-card">
                    <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.9rem' }}>
                      About Cohen's Kappa (κ) in Qualitative Fintech Research:
                    </span>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '6px', lineHeight: 1.5 }}>
                      Simple percent agreement can be deceptively high due to class imbalance (e.g. if 60% of complaints are about market dip panic, a naive model guessing market dip would achieve 60% accuracy). Cohen's Kappa factors out chance probability ($P_e$), ensuring the system only scores high when it accurately distinguishes nuanced complaints.
                    </p>
                  </div>
                </>
              ) : (
                <div className="eval-loading">Loading metrics...</div>
              )}
            </div>
          )}

          {/* TAB 2: CONFUSION MATRIX */}
          {activeTab === 'matrix' && (
            <div className="eval-tab-content">
              <div className="matrix-controls-bar">
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Inspect Field:
                </span>
                {['theme', 'journey_stage', 'what_they_did'].map((f) => (
                  <button
                    key={f}
                    type="button"
                    className={`filter-pill ${matrixField === f ? 'active' : ''}`}
                    onClick={() => handleFieldChange(f)}
                  >
                    {f === 'theme' ? 'Dynamic Theme' : f === 'journey_stage' ? 'Journey Stage' : 'Action Taken'}
                  </button>
                ))}
              </div>

              {matrixData && matrixData.labels?.length > 0 ? (
                <div className="matrix-table-card">
                  <div className="matrix-axis-label horizontal">
                    <span>AI Predicted Label ➔</span>
                  </div>
                  <div className="matrix-table-wrapper">
                    <table className="confusion-matrix-table">
                      <thead>
                        <tr>
                          <th className="corner-th">Golden Truth ⬇</th>
                          {matrixData.labels.map((lbl, idx) => (
                            <th key={idx} className="col-header-th" title={lbl}>
                              <div className="rotated-th">{lbl}</div>
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {matrixData.labels.map((rowLabel, rIdx) => (
                          <tr key={rIdx}>
                            <td className="row-header-td" title={rowLabel}>
                              {rowLabel}
                            </td>
                            {matrixData.matrix[rIdx]?.map((val, cIdx) => {
                              const isDiagonal = rIdx === cIdx;
                              let cellClass = 'matrix-cell';
                              if (isDiagonal && val > 0) cellClass += ' cell-diagonal';
                              else if (!isDiagonal && val > 0) cellClass += ' cell-off-diagonal';
                              return (
                                <td key={cIdx} className={cellClass} title={`Golden: "${rowLabel}" | AI: "${matrixData.labels[cIdx]}"`}>
                                  {val > 0 ? val : '·'}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="matrix-legend">
                    <span className="legend-item"><span className="legend-box match"></span> Green: Accurate Agreement</span>
                    <span className="legend-item"><span className="legend-box mismatch"></span> Amber: Divergent Classification</span>
                  </div>
                </div>
              ) : (
                <div className="eval-loading">No matrix data available yet.</div>
              )}
            </div>
          )}

          {/* TAB 3: DISAGREEMENT INSPECTOR */}
          {activeTab === 'disagreements' && (
            <div className="eval-tab-content">
              {disagreements.length === 0 ? (
                <div className="empty-disagreements">
                  <CheckCircle2 size={32} style={{ color: '#10b981' }} />
                  <p style={{ fontWeight: 600, color: '#f8fafc', marginTop: '8px' }}>
                    Zero Active Disagreements!
                  </p>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    AI predictions currently match all verified Golden Benchmark hand-labels.
                  </span>
                </div>
              ) : (
                <div className="disagreements-list">
                  {disagreements.map((d) => (
                    <div key={d.post_id} className="disagreement-card">
                      <div className="disagreement-header">
                        <div className="d-post-meta">
                          <span className="badge badge-source">{d.platform}</span>
                          <span className="badge badge-source">{d.source}</span>
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>ID: {d.post_id}</span>
                        </div>
                        <div className="d-field-badges">
                          {d.disagreed_fields.map((fld) => (
                            <span key={fld} className="d-mismatch-badge">
                              ⚠ Mismatched: {fld}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Raw Post Excerpt with Verbatim Evidence */}
                      <div className="d-comment-body">
                        <span>"{d.raw_text}"</span>
                      </div>

                      {/* Side-by-Side Comparison Grid */}
                      <div className="d-comparison-grid">
                        {/* Left: AI Predicted Tag */}
                        <div className="comparison-side ai-side">
                          <div className="side-title">
                            <Sparkles size={14} className="text-indigo-400" />
                            <span>AI Prediction</span>
                          </div>
                          <div className="side-fields">
                            <div className="side-field-row">
                              <span className="label">Theme:</span>
                              <strong className={d.disagreed_fields.includes('theme') ? 'diff-val' : ''}>{d.ai.theme}</strong>
                            </div>
                            <div className="side-field-row">
                              <span className="label">Journey Stage:</span>
                              <strong className={d.disagreed_fields.includes('journey_stage') ? 'diff-val' : ''}>{d.ai.journey_stage}</strong>
                            </div>
                            <div className="side-field-row">
                              <span className="label">Action:</span>
                              <strong className={d.disagreed_fields.includes('what_they_did') ? 'diff-val' : ''}>{d.ai.what_they_did}</strong>
                            </div>
                            <div className="side-field-row">
                              <span className="label">Fixer:</span>
                              <strong className={d.disagreed_fields.includes('who_can_fix_it') ? 'diff-val' : ''}>{d.ai.who_can_fix_it}</strong>
                            </div>
                          </div>
                          <button
                            type="button"
                            className="btn-resolve-accept"
                            onClick={() => handleResolve(d.post_id, 'accept_ai')}
                            disabled={resolvingId === d.post_id}
                          >
                            <Check size={14} />
                            <span>Accept AI Prediction</span>
                          </button>
                        </div>

                        {/* Right: Golden Benchmark */}
                        <div className="comparison-side golden-side">
                          <div className="side-title">
                            <ShieldCheck size={14} className="text-emerald-400" />
                            <span>Golden Benchmark (PM Truth)</span>
                          </div>
                          <div className="side-fields">
                            <div className="side-field-row">
                              <span className="label">Theme:</span>
                              <strong>{d.golden.theme}</strong>
                            </div>
                            <div className="side-field-row">
                              <span className="label">Journey Stage:</span>
                              <strong>{d.golden.journey_stage}</strong>
                            </div>
                            <div className="side-field-row">
                              <span className="label">Action:</span>
                              <strong>{d.golden.what_they_did}</strong>
                            </div>
                            <div className="side-field-row">
                              <span className="label">Fixer:</span>
                              <strong>{d.golden.who_can_fix_it}</strong>
                            </div>
                            {d.golden.notes && (
                              <div className="side-notes">
                                <em>PM Note: {d.golden.notes}</em>
                              </div>
                            )}
                          </div>
                          <button
                            type="button"
                            className="btn-resolve-keep"
                            onClick={() => handleResolve(d.post_id, 'override_golden')}
                            disabled={resolvingId === d.post_id}
                          >
                            <CheckCircle2 size={14} />
                            <span>Keep Golden Benchmark</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
