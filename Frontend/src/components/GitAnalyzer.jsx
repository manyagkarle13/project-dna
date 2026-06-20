import React, { useState } from 'react';
import { analyzeGitLink } from '../services/apiService';
import './GitAnalyzer.css';

function GitAnalyzer() {
  const [gitLink, setGitLink] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysis, setAnalysis] = useState(null);

  const handleAnalyze = async (e) => {
    e.preventDefault();

    if (!gitLink.trim()) {
      setError('Please enter a git link');
      return;
    }

    setLoading(true);
    setError('');
    setAnalysis(null);

    try {
      const result = await analyzeGitLink(gitLink);
      setAnalysis(result);

      // Optionally redirect to conversation
      if (result.conversation_id) {
        setTimeout(() => {
          window.location.href = `/dashboard`;
        }, 2000);
      }
    } catch (err) {
      setError(err.message || 'Failed to analyze repository');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="git-analyzer-container">
      <div className="git-analyzer-card">
        <h2>🔍 Analyze Git Repository</h2>
        <p className="subtitle">Paste a GitHub/GitLab link to analyze deployment issues and bugs</p>

        <form onSubmit={handleAnalyze} className="analyzer-form">
          <div className="form-group">
            <input
              type="text"
              placeholder="https://github.com/owner/repo or https://github.com/owner/repo.git"
              value={gitLink}
              onChange={(e) => setGitLink(e.target.value)}
              disabled={loading}
              className="git-input"
            />
            <button type="submit" disabled={loading} className="analyze-btn">
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Analyzing...
                </>
              ) : (
                '📊 Analyze'
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="error-message">
            <span>❌ {error}</span>
          </div>
        )}

        {analysis && (
          <div className="analysis-result">
            <div className="success-message">
              ✅ Analysis Complete!
            </div>

            <div className="result-card">
              <h3>{analysis.analysis.repo_name}</h3>

              <div className="result-grid">
                <div className="result-item">
                  <label>Tech Stack</label>
                  <p className="result-value">
                    {analysis.analysis.tech_stack.length > 0
                      ? analysis.analysis.tech_stack.join(', ')
                      : 'Not detected'}
                  </p>
                </div>

                <div className="result-item">
                  <label>Issues Found</label>
                  <p className="result-value">
                    {analysis.analysis.bugs_found.length}
                  </p>
                </div>

                <div className="result-item">
                  <label>Fixes Ready</label>
                  <p className="result-value">
                    {analysis.analysis.fixes_suggested.length}
                  </p>
                </div>
              </div>

              {analysis.analysis.bugs_found.length > 0 && (
                <div className="bugs-section">
                  <h4>🐛 Issues Found:</h4>
                  <ul className="bugs-list">
                    {analysis.analysis.bugs_found.map((bug, idx) => (
                      <li key={idx} className={`bug-item severity-${bug.severity}`}>
                        <span className="bug-file">{bug.file}</span>
                        <span className="bug-message">{bug.issue}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {analysis.analysis.fixes_suggested.length > 0 && (
                <div className="fixes-section">
                  <h4>🔧 Fixes Suggested:</h4>
                  <ul className="fixes-list">
                    {analysis.analysis.fixes_suggested.map((fix, idx) => (
                      <li key={idx} className="fix-item">✅ {fix}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="redirect-message">
                <p>Redirecting to chat in 2 seconds...</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default GitAnalyzer;
