import React from 'react';
import { Database, CheckCircle2, Sparkles, Building2, ChevronRight } from 'lucide-react';

export default function MetricsBar({ stats, onOpenEvaluation }) {
  const totalPosts = stats?.total_posts || 0;
  const goldenCount = stats?.golden_count || 0;
  const agreementRate = stats?.agreement_rate || 0;
  const platformCounts = stats?.platform_counts || {};

  // Find top platform
  const topPlatform = Object.entries(platformCounts).sort((a, b) => b[1] - a[1])[0] || ['Groww', 0];

  return (
    <div className="metrics-strip">
      <div className="metric-card">
        <div className="metric-icon-box" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8' }}>
          <Database size={22} />
        </div>
        <div className="metric-info">
          <span className="metric-label">Ingested Public Posts</span>
          <span className="metric-val">{totalPosts.toLocaleString()}</span>
        </div>
      </div>

      <div 
        className="metric-card metric-card-interactive"
        onClick={onOpenEvaluation}
        title="Click to inspect Cohen's Kappa, Confusion Matrix & Disagreements"
      >
        <div className="metric-icon-box" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399' }}>
          <CheckCircle2 size={22} />
        </div>
        <div className="metric-info">
          <div className="metric-label-row">
            <span className="metric-label">Golden Truth Benchmark</span>
            <ChevronRight size={13} className="text-emerald-400" />
          </div>
          <span className="metric-val">{goldenCount.toLocaleString()} verified</span>
        </div>
      </div>

      <div 
        className="metric-card metric-card-interactive"
        onClick={onOpenEvaluation}
        title="Click to view full Cohen's Kappa reliability breakdown"
      >
        <div className="metric-icon-box" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24' }}>
          <Sparkles size={22} />
        </div>
        <div className="metric-info">
          <div className="metric-label-row">
            <span className="metric-label">Reliability (Cohen's κ)</span>
            <ChevronRight size={13} className="text-amber-400" />
          </div>
          <span className="metric-val">
            {goldenCount > 0 ? `${agreementRate}% match` : 'Seed Golden Set'}
          </span>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-icon-box" style={{ background: 'rgba(6, 182, 212, 0.15)', color: '#38bdf8' }}>
          <Building2 size={22} />
        </div>
        <div className="metric-info">
          <span className="metric-label">Top Platform Volume</span>
          <span className="metric-val">{topPlatform[0]} ({topPlatform[1]})</span>
        </div>
      </div>
    </div>
  );
}
