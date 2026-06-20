import './LandingPage.css';

export default function LandingPage({ onSignIn }) {
  return (
    <div className="landing-container">
      {/* Header */}
      <header className="landing-header">
        <div className="landing-header-content">
          <div className="landing-logo">
            <span className="logo-icon">🧬</span>
            <span className="logo-text">Project DNA</span>
          </div>
          <button className="landing-signin-btn" onClick={onSignIn}>
            Sign In
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="landing-hero">
        <div className="landing-hero-content">
          <h1 className="landing-title">
            AI-Powered Code Analysis <br />
            <span className="highlight">Right in Your Chat</span>
          </h1>
          <p className="landing-subtitle">
            Analyze repositories, find bugs, generate code reviews, and create pull requests—all through conversation. No buttons, no complexity.
          </p>
          <button className="landing-cta-btn" onClick={onSignIn}>
            Get Started Free
          </button>
        </div>
      </section>

      {/* Features Section */}
      <section className="landing-features">
        <h2>What You Can Do</h2>
        <div className="landing-features-grid">
          <div className="landing-feature-card">
            <div className="feature-icon">💬</div>
            <h3>Chat About Code</h3>
            <p>Paste a GitHub link and ask questions. Our AI understands your repository instantly.</p>
          </div>

          <div className="landing-feature-card">
            <div className="feature-icon">🐛</div>
            <h3>Find Bugs</h3>
            <p>AI-powered security and performance analysis. Discover issues before they reach production.</p>
          </div>

          <div className="landing-feature-card">
            <div className="feature-icon">📝</div>
            <h3>Code Reviews</h3>
            <p>Get instant, detailed code reviews. Understand what could be improved and why.</p>
          </div>

          <div className="landing-feature-card">
            <div className="feature-icon">🔧</div>
            <h3>Auto Fixes</h3>
            <p>Ask for a fix and get automatic pull requests created on your GitHub repo.</p>
          </div>

          <div className="landing-feature-card">
            <div className="feature-icon">📊</div>
            <h3>Repository Analysis</h3>
            <p>Understand your codebase structure, tech stack, and architecture at a glance.</p>
          </div>

          <div className="landing-feature-card">
            <div className="feature-icon">💰</div>
            <h3>100% Free</h3>
            <p>Powered by Hugging Face. No API costs. No monthly fees. Ever.</p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="landing-how-it-works">
        <h2>How It Works</h2>
        <div className="landing-steps">
          <div className="landing-step">
            <div className="step-number">1</div>
            <h3>Sign In</h3>
            <p>Create an account with email or GitHub</p>
          </div>
          <div className="landing-step-arrow">→</div>
          <div className="landing-step">
            <div className="step-number">2</div>
            <h3>Paste a Repo Link</h3>
            <p>Drop any GitHub URL in the chat</p>
          </div>
          <div className="landing-step-arrow">→</div>
          <div className="landing-step">
            <div className="step-number">3</div>
            <h3>Ask Questions</h3>
            <p>"Find bugs" or "Create a fix"</p>
          </div>
          <div className="landing-step-arrow">→</div>
          <div className="landing-step">
            <div className="step-number">4</div>
            <h3>Get PRs Auto-Created</h3>
            <p>Fix approved? PR ready on GitHub</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p>Project DNA © 2026 | Powered by Hugging Face AI</p>
      </footer>
    </div>
  );
}
