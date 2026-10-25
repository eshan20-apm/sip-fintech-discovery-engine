import React from 'react';
import { CheckCircle2, Sparkles, MessageSquare } from 'lucide-react';

export default function PostsTable({ posts, selectedPost, onSelectPost, isLoading, activeQuery }) {
  if (isLoading) {
    return (
      <div className="table-card">
        <div className="empty-state">
          <Sparkles className="empty-icon animate-pulse" style={{ color: '#818cf8' }} />
          <p style={{ fontWeight: 600, color: '#f8fafc', fontSize: '1rem' }}>
            Analyzing Query & Ingesting Public Comments...
          </p>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            LLM is reading Play Store reviews & Reddit threads, tagging themes in 2-3 words, and identifying investor actions.
          </span>
        </div>
      </div>
    );
  }

  if (!posts || posts.length === 0) {
    return (
      <div className="table-card">
        <div className="empty-state">
          <MessageSquare className="empty-icon" />
          <p style={{ fontWeight: 600, color: '#f8fafc', fontSize: '1rem' }}>No research results found</p>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Enter a prompt above (e.g. "Why do beginners cancel SIPs during market downturns?") or select a suggested research question.
          </span>
        </div>
      </div>
    );
  }

  const getPlatformBadge = (platform) => {
    switch (platform) {
      case 'Groww':
        return <span className="badge badge-groww">Groww</span>;
      case 'Zerodha':
        return <span className="badge badge-zerodha">Zerodha Coin</span>;
      case 'AngelOne':
        return <span className="badge badge-angelone">Angel One</span>;
      case 'INDmoney':
        return <span className="badge badge-indmoney">INDmoney</span>;
      case 'PaytmMoney':
        return <span className="badge badge-paytmmoney">Paytm Money</span>;
      default:
        return <span className="badge badge-source">{platform || 'General MF'}</span>;
    }
  };

  const getSourceBadge = (source) => {
    switch (source) {
      case 'youtube':
        return <span className="badge badge-youtube">▶ YouTube</span>;
      case 'reddit':
        return <span className="badge badge-source">Reddit</span>;
      default:
        return <span className="badge badge-source">Play Store</span>;
    }
  };

  return (
    <div className="table-card">
      <div className="table-header-bar">
        <div className="table-title-area">
          <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#fff' }}>
            {activeQuery ? `Research Results: "${activeQuery}"` : "Structured Investor Feedback Feed"}
          </span>
          <span className="table-count-badge">{posts.length} Comments Enriched</span>
          {activeQuery && (
            <span className="hybrid-rag-indicator" title="Ranked via Dense Semantic Vectors + Sparse SQLite FTS5 BM25">
              ⚡ Hybrid RAG Active
            </span>
          )}
        </div>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Click any row to view full verbatim context & refine Golden Benchmark tags
        </span>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Platform</th>
              <th>Source</th>
              <th>Date</th>
              <th>Raw Comment</th>
              <th>Dynamic Theme (2-3 Words)</th>
              <th>Journey Stage</th>
              <th>Action Taken</th>
            </tr>
          </thead>
          <tbody>
            {posts.map((post) => {
              const isSelected = selectedPost?.id === post.id;
              const isGolden = post.is_hand_labelled === 1;
              
              // Effective tags (Golden override takes precedence)
              const theme = isGolden ? post.golden_theme : post.ai_theme;
              const journey = isGolden ? post.golden_journey_stage : post.ai_journey_stage;
              const action = isGolden ? post.golden_what_they_did : post.ai_what_they_did;
              const pubDate = post.published_at ? post.published_at.slice(0, 10) : 'Live';

              return (
                <tr 
                  key={post.id}
                  className={`table-row ${isSelected ? 'selected' : ''}`}
                  onClick={() => onSelectPost(post)}
                >
                  {/* Status Badge */}
                  <td>
                    {isGolden ? (
                      <span className="badge badge-golden" title="Hand-verified golden benchmark">
                        <CheckCircle2 size={12} />
                        <span>Golden</span>
                      </span>
                    ) : (
                      <span className="badge badge-ai" title="Dynamically tagged by LLM">
                        <Sparkles size={12} />
                        <span>AI Tagged</span>
                      </span>
                    )}
                  </td>

                  {/* Platform */}
                  <td>{getPlatformBadge(post.platform)}</td>

                  {/* Source */}
                  <td>
                    {getSourceBadge(post.source)}
                  </td>

                  {/* Date */}
                  <td style={{ color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {pubDate}
                  </td>

                  {/* Raw Comment */}
                  <td>
                    <div className="raw-text-cell" title={post.raw_text}>
                      {post.raw_text}
                    </div>
                  </td>

                  {/* Dynamic Theme (2-3 words) */}
                  <td>
                    <span className="badge badge-dynamic-theme" title={theme || 'Unclear'}>
                      {theme || 'Unclear'}
                    </span>
                  </td>

                  {/* Dynamic Journey Stage */}
                  <td>
                    <span className="badge badge-dynamic-stage" title={journey || 'Unclear'}>
                      {journey || 'Active SIP Phase'}
                    </span>
                  </td>

                  {/* Dynamic Action Taken */}
                  <td>
                    <span className="badge badge-dynamic-action" title={action || 'Unclear'}>
                      {action || 'Unsure'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
