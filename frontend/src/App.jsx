import React, { useState, useEffect, useCallback } from 'react';
import { Layers, Key, Check, ShieldCheck, Activity } from 'lucide-react';
import BiasBanner from './components/BiasBanner';
import MetricsBar from './components/MetricsBar';
import ResearchPromptBar from './components/ResearchPromptBar';
import PostsTable from './components/PostsTable';
import DetailDrawer from './components/DetailDrawer';
import EvaluationDashboardModal from './components/EvaluationDashboardModal';

export default function App() {
  const [posts, setPosts] = useState([]);
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [selectedPost, setSelectedPost] = useState(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [showEvalModal, setShowEvalModal] = useState(false);

  // Conversational research query states
  const [activeQuery, setActiveQuery] = useState('');
  const [queryAnalysis, setQueryAnalysis] = useState(null);
  const [platform, setPlatform] = useState('all');
  const [status, setStatus] = useState('all');

  // Settings modal
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [apiKeyStatus, setApiKeyStatus] = useState(null);

  const loadStats = useCallback(async () => {
    try {
      const resp = await fetch('/api/stats');
      if (resp.ok) {
        const data = await resp.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  }, []);

  const loadPosts = useCallback(async (scopePlatform = platform, scopeStatus = status) => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (scopePlatform !== 'all') params.append('platform', scopePlatform);
      if (scopeStatus !== 'all') params.append('status', scopeStatus);
      if (activeQuery.trim()) params.append('search_query', activeQuery.trim());

      const resp = await fetch(`/api/posts?${params.toString()}`);
      if (resp.ok) {
        const data = await resp.json();
        setPosts(data.posts || []);
      }
    } catch (err) {
      console.error('Failed to load posts:', err);
    } finally {
      setIsLoading(false);
    }
  }, [activeQuery, platform, status]);

  // Initial load & global keyboard shortcut handlers
  useEffect(() => {
    loadPosts();
    loadStats();

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsDrawerOpen(false);
        setShowEvalModal(false);
        setShowApiKeyModal(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Conversational Research Query Handler (ChatGPT / Gemini style)
  const handleRunResearch = async (queryText) => {
    setIsLoading(true);
    setActiveQuery(queryText);
    try {
      const payload = {
        query: queryText,
        platforms: platform === 'all' ? null : [platform],
        limit: 25
      };

      const resp = await fetch('/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (resp.ok) {
        const data = await resp.json();
        setQueryAnalysis(data.analysis);
        setPosts(data.posts || []);
        loadStats();
      } else {
        throw new Error(`Server returned ${resp.status}`);
      }
    } catch (err) {
      console.error('Research error:', err);
      // Fallback: search existing posts
      loadPosts(platform, status);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlatformChange = (newPlatform) => {
    setPlatform(newPlatform);
    loadPosts(newPlatform, status);
  };

  const handleStatusChange = (newStatus) => {
    setStatus(newStatus);
    loadPosts(platform, newStatus);
  };

  const handleSelectPost = (post) => {
    setSelectedPost(post);
    setIsDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setIsDrawerOpen(false);
  };

  const handleSaveGoldenTag = async (goldenData) => {
    const resp = await fetch('/api/golden-tag', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(goldenData)
    });

    if (resp.ok) {
      const result = await resp.json();
      const updatedTag = result.golden_tag;

      // Update post in table view
      setPosts(prev => prev.map(p => {
        if (p.id === updatedTag.post_id) {
          return {
            ...p,
            is_hand_labelled: 1,
            golden_theme: updatedTag.theme,
            golden_journey_stage: updatedTag.journey_stage,
            golden_what_they_did: updatedTag.what_they_did,
            golden_who_they_are: updatedTag.who_they_are,
            golden_who_can_fix_it: updatedTag.who_can_fix_it,
            golden_evidence_quote: updatedTag.evidence_quote,
            golden_notes: updatedTag.notes
          };
        }
        return p;
      }));

      // Update selectedPost as well
      setSelectedPost(prev => ({
        ...prev,
        is_hand_labelled: 1,
        golden_theme: updatedTag.theme,
        golden_journey_stage: updatedTag.journey_stage,
        golden_what_they_did: updatedTag.what_they_did,
        golden_who_they_are: updatedTag.who_they_are,
        golden_who_can_fix_it: updatedTag.who_can_fix_it,
        golden_evidence_quote: updatedTag.evidence_quote,
        golden_notes: updatedTag.notes
      }));

      loadStats();
    }
  };

  const handleExportExcel = async () => {
    setIsExporting(true);
    try {
      const params = new URLSearchParams();
      if (activeQuery.trim()) params.append('search_query', activeQuery.trim());
      if (platform !== 'all') params.append('platform', platform);
      if (status !== 'all') params.append('status', status);

      const response = await fetch(`/api/export?${params.toString()}`);
      if (!response.ok) throw new Error('Failed to generate export');

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `sip_discovery_research_${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error('Export error:', err);
      alert('Failed to export Excel file. Please check backend connection.');
    } finally {
      setIsExporting(false);
    }
  };

  const handleSaveApiKey = async () => {
    try {
      const resp = await fetch('/api/settings/api-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKeyInput })
      });
      if (resp.ok) {
        setApiKeyStatus('Updated successfully!');
        setTimeout(() => {
          setShowApiKeyModal(false);
          setApiKeyStatus(null);
        }, 1500);
      }
    } catch (e) {
      setApiKeyStatus('Error saving key');
    }
  };

  return (
    <div className="app-container">
      {/* Top Sticky Navbar */}
      <header className="top-navbar">
        <div className="brand-section">
          <div className="brand-logo-badge">
            <Layers size={20} color="#fff" />
          </div>
          <div className="brand-title">
            <span>SIP Investor Behavior Discovery Engine</span>
            <span className="brand-tag">Prompt-Driven AI</span>
          </div>
        </div>

        <div className="nav-actions">
          <button 
            className="btn-secondary btn-benchmark-trigger"
            onClick={() => setShowEvalModal(true)}
            title="Inspect Golden Benchmark, Cohen's Kappa, Confusion Matrix & Disagreements"
          >
            <ShieldCheck size={15} style={{ color: '#10b981' }} />
            <span>Golden Benchmark (κ)</span>
            {stats?.golden_count > 0 && (
              <span className="badge-kappa-nav">
                {stats.golden_count} verified
              </span>
            )}
          </button>

          <button 
            className="btn-secondary"
            onClick={() => setShowApiKeyModal(true)}
            title="Configure Gemini API Key"
          >
            <Key size={15} />
            <span>LLM Settings</span>
          </button>
        </div>
      </header>

      {/* Research Complainant Bias Warning Banner */}
      <BiasBanner />

      {/* Main Research Workbench */}
      <main className="workbench-body">
        {/* Metrics Overview Strip */}
        <MetricsBar 
          stats={stats} 
          onOpenEvaluation={() => setShowEvalModal(true)} 
        />

        {/* Conversational Prompt Space (ChatGPT / Gemini style) */}
        <ResearchPromptBar 
          onRunResearch={handleRunResearch}
          isLoading={isLoading}
          platform={platform}
          onPlatformChange={handlePlatformChange}
          status={status}
          onStatusChange={handleStatusChange}
          onExportExcel={handleExportExcel}
          isExporting={isExporting}
          queryAnalysis={queryAnalysis}
        />

        {/* Structured Data Grid with Dynamic Theme (2-3 words), Journey Stage, and Action */}
        <PostsTable 
          posts={posts}
          selectedPost={selectedPost}
          onSelectPost={handleSelectPost}
          isLoading={isLoading}
          activeQuery={activeQuery}
        />
      </main>

      {/* Slide-Over Detail Drawer with Verbatim Quote Highlight & Golden Benchmark Tag Editor */}
      <DetailDrawer 
        post={selectedPost}
        isOpen={isDrawerOpen}
        onClose={handleCloseDrawer}
        onSaveGoldenTag={handleSaveGoldenTag}
      />

      {/* Golden Benchmark & Cohen's Kappa Evaluation Dashboard Modal */}
      <EvaluationDashboardModal 
        isOpen={showEvalModal}
        onClose={() => setShowEvalModal(false)}
        onRefreshData={() => {
          loadPosts();
          loadStats();
        }}
      />

      {/* LLM API Key Configuration Modal */}
      {showApiKeyModal && (
        <div className="modal-backdrop" onClick={() => setShowApiKeyModal(false)}>
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#fff' }}>
                LLM Configuration (Gemini API)
              </h3>
              <button onClick={() => setShowApiKeyModal(false)} className="btn-close">
                ×
              </button>
            </div>
            <div className="modal-body">
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                The engine includes an intelligent dynamic heuristic tagger by default. To enable full generative analysis and dynamic query extraction via <strong>Google Gemini 2.5 Flash</strong>, paste your free Google AI Studio API key below:
              </p>
              <div className="field-group">
                <label className="field-label">GEMINI_API_KEY</label>
                <input 
                  type="password"
                  className="field-input"
                  placeholder="AIzaSy..."
                  value={apiKeyInput}
                  onChange={e => setApiKeyInput(e.target.value)}
                />
              </div>
              {apiKeyStatus && (
                <div style={{ color: '#34d399', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Check size={16} />
                  <span>{apiKeyStatus}</span>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowApiKeyModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleSaveApiKey}>
                Save Key
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
