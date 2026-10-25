import React, { useState, useEffect } from 'react';
import { X, ExternalLink, CheckCircle2, Sparkles, Save, ShieldCheck } from 'lucide-react';

export default function DetailDrawer({ post, isOpen, onClose, onSaveGoldenTag }) {
  if (!isOpen || !post) return null;

  const isGolden = post.is_hand_labelled === 1;

  // Form states initialized with current golden override or dynamic AI tag
  const [theme, setTheme] = useState('');
  const [journeyStage, setJourneyStage] = useState('');
  const [whatTheyDid, setWhatTheyDid] = useState('');
  const [whoTheyAre, setWhoTheyAre] = useState('');
  const [whoCanFixIt, setWhoCanFixIt] = useState('');
  const [evidenceQuote, setEvidenceQuote] = useState('');
  const [notes, setNotes] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (post) {
      setTheme(post.golden_theme || post.ai_theme || 'Retail investor friction');
      setJourneyStage(post.golden_journey_stage || post.ai_journey_stage || 'Active SIP Phase');
      setWhatTheyDid(post.golden_what_they_did || post.ai_what_they_did || 'Unsure');
      setWhoTheyAre(post.golden_who_they_are || post.ai_who_they_are || 'Retail investor');
      setWhoCanFixIt(post.golden_who_can_fix_it || post.ai_who_can_fix_it || 'Fintech Platform');
      setEvidenceQuote(post.golden_evidence_quote || post.ai_evidence_quote || '');
      setNotes(post.golden_notes || '');
      setSaveSuccess(false);
    }
  }, [post]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSaveGoldenTag({
        post_id: post.id,
        theme,
        journey_stage: journeyStage,
        what_they_did: whatTheyDid,
        who_they_are: whoTheyAre,
        who_can_fix_it: whoCanFixIt,
        evidence_quote: evidenceQuote,
        notes
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to save golden tag:", err);
    } finally {
      setIsSaving(false);
    }
  };

  // Render raw text with verbatim quote highlighted
  const renderHighlightedText = () => {
    const raw = post.raw_text || '';
    const quote = evidenceQuote || post.ai_evidence_quote;

    if (!quote || !raw.includes(quote)) {
      return <span>{raw}</span>;
    }

    const parts = raw.split(quote);
    return (
      <span>
        {parts[0]}
        <mark className="verbatim-highlight" title="Verbatim Evidence Substring">
          {quote}
        </mark>
        {parts.slice(1).join(quote)}
      </span>
    );
  };

  return (
    <>
      <div className={`drawer-backdrop ${isOpen ? 'open' : ''}`} onClick={onClose} />
      <div className={`drawer-panel ${isOpen ? 'open' : ''}`}>
        <div className="drawer-header">
          <div className="drawer-title-group">
            <div className="drawer-title">
              <span>Comment Inspection</span>
              {isGolden ? (
                <span className="badge badge-golden">
                  <CheckCircle2 size={12} />
                  <span>Golden Benchmark</span>
                </span>
              ) : (
                <span className="badge badge-ai">
                  <Sparkles size={12} />
                  <span>AI Tagged</span>
                </span>
              )}
            </div>
            <span className="drawer-subtitle">
              ID: {post.id} • {post.platform} • {post.source === 'playstore' ? 'Google Play Store' : post.source === 'youtube' ? 'YouTube Comment' : 'Reddit'}
            </span>
          </div>
          <button onClick={onClose} className="btn-close" title="Close Panel (Esc)">
            <X size={20} />
          </button>
        </div>

        <div className="drawer-content">
          {/* Section 1: Raw Text & Verbatim Quote */}
          <div className="drawer-section">
            <div className="section-title">
              <span>Full Raw Comment & Verbatim Grounding</span>
            </div>
            <div className="raw-quote-card">
              {renderHighlightedText()}
            </div>
            {post.url && (
              <a 
                href={post.url} 
                target="_blank" 
                rel="noopener noreferrer" 
                className="external-link-btn"
              >
                <span>View original public comment on {post.source === 'playstore' ? 'Play Store' : post.source === 'youtube' ? 'YouTube' : 'Reddit'}</span>
                <ExternalLink size={14} />
              </a>
            )}
          </div>

          {/* Section 2: Dynamic Golden Benchmark Editor */}
          <div className="drawer-section">
            <div className="section-title">
              <ShieldCheck size={16} style={{ color: '#10b981' }} />
              <span>Golden Benchmark Editor (Refine Dynamic Tags)</span>
            </div>

            <div className="tag-editor-grid">
              {/* Field 1: Theme (2-3 words dynamic) */}
              <div className="field-group">
                <label className="field-label">
                  <span>Dynamic Theme (2–3 Words)</span>
                  <span className="ai-tag-hint">AI: {post.ai_theme}</span>
                </label>
                <input 
                  type="text" 
                  className="field-input" 
                  value={theme} 
                  onChange={(e) => setTheme(e.target.value)}
                  placeholder="e.g. Market dip panic, Autopay bounce charge"
                />
              </div>

              {/* Field 2: Journey Stage (dynamic) */}
              <div className="field-group">
                <label className="field-label">
                  <span>Journey Stage</span>
                  <span className="ai-tag-hint">AI: {post.ai_journey_stage}</span>
                </label>
                <input 
                  type="text" 
                  className="field-input" 
                  value={journeyStage} 
                  onChange={(e) => setJourneyStage(e.target.value)}
                  placeholder="e.g. 1st Month Bull Run, Months 2-6 Market Dip, KYC Onboarding"
                />
              </div>

              {/* Field 3: Action Taken (dynamic) */}
              <div className="field-group">
                <label className="field-label">
                  <span>Action Taken</span>
                  <span className="ai-tag-hint">AI: {post.ai_what_they_did}</span>
                </label>
                <input 
                  type="text" 
                  className="field-input" 
                  value={whatTheyDid} 
                  onChange={(e) => setWhatTheyDid(e.target.value)}
                  placeholder="e.g. Cancelled SIP, Switched to Coin, Paused indefinitely"
                />
              </div>

              {/* Field 4: Persona */}
              <div className="field-group">
                <label className="field-label">
                  <span>Investor Persona</span>
                  <span className="ai-tag-hint">AI: {post.ai_who_they_are}</span>
                </label>
                <input 
                  type="text" 
                  className="field-input" 
                  value={whoTheyAre} 
                  onChange={(e) => setWhoTheyAre(e.target.value)}
                  placeholder="e.g. Salaried beginner 24yo, Seasoned DIY investor"
                />
              </div>

              {/* Field 5: Verbatim Evidence Quote */}
              <div className="field-group">
                <label className="field-label">
                  <span>Exact Verbatim Evidence Quote</span>
                </label>
                <input 
                  type="text" 
                  className="field-input" 
                  value={evidenceQuote} 
                  onChange={(e) => setEvidenceQuote(e.target.value)}
                  placeholder="Verbatim quote substring from the raw comment"
                />
              </div>

              {/* PM Rationale / Notes */}
              <div className="field-group">
                <label className="field-label">
                  <span>PM Benchmark Rationale / Notes</span>
                </label>
                <textarea 
                  className="field-input" 
                  rows={2} 
                  value={notes} 
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Why did you classify it this way? (e.g. User explicitly confused Demat with SOA)"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="drawer-footer">
          <div>
            {saveSuccess && (
              <span className="saved-toast-indicator">
                <CheckCircle2 size={16} />
                <span>Saved to Golden Truth Set!</span>
              </span>
            )}
          </div>
          <button 
            className="btn-success"
            onClick={handleSave}
            disabled={isSaving}
          >
            <Save size={16} />
            <span>{isSaving ? 'Saving...' : 'Save as Golden Benchmark'}</span>
          </button>
        </div>
      </div>
    </>
  );
}
