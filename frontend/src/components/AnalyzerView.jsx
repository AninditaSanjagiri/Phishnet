import { useState } from 'react'
import { analyzeUrl } from '../utils/api.js'
import URLInput from './URLInput.jsx'
import VerdictBanner from './VerdictBanner.jsx'
import AgentCard from './AgentCard.jsx'
import ScreenshotPanel from './ScreenshotPanel.jsx'
import FusionPanel from './FusionPanel.jsx'
import LoadingState from './LoadingState.jsx'
import './AnalyzerView.css'

export default function AnalyzerView({ onResult, lastResult }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(lastResult)

  async function handleAnalyze(url) {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await analyzeUrl(url)
      setResult(data)
      onResult(data)
    } catch (err) {
      setError(err.message || 'Analysis failed. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="analyzer">
      {/* Hero */}
      <div className="analyzer-hero">
        <h1 className="hero-title">
          Detect Phishing with
          <span className="hero-accent"> Multimodal AI</span>
        </h1>
        <p className="hero-sub">
          URL heuristics · DistilBERT text analysis · MobileNetV3 visual scan
        </p>
      </div>

      {/* Input */}
      <URLInput onSubmit={handleAnalyze} loading={loading} />

      {/* Error */}
      {error && (
        <div className="error-bar">
          <span className="error-icon">⚠</span>
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && <LoadingState />}

      {/* Results */}
      {result && !loading && (
        <div className="results" style={{ animation: 'fade-up 0.4s ease' }}>
          <VerdictBanner result={result} />

          <div className="results-grid">
            <AgentCard
              title="URL Agent"
              subtitle="Random Forest · Heuristics"
              icon="🔗"
              agentResult={result.url_agent}
              color="accent"
            />
            <AgentCard
              title="Text Agent"
              subtitle="DistilBERT · HTML content"
              icon="📄"
              agentResult={result.text_agent}
              color="purple"
            />
            <AgentCard
              title="Image Agent"
              subtitle="MobileNetV3 · Screenshot"
              icon="🖼"
              agentResult={result.image_agent}
              color="warn"
            />
          </div>

          <div className="results-bottom">
            <FusionPanel result={result} />
            {(result.screenshot_base64 || result.gradcam_base64) && (
              <ScreenshotPanel result={result} />
            )}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!result && !loading && !error && (
        <div className="empty-state">
          <div className="empty-grid">
            {['URL features', 'Text semantics', 'Visual layout'].map((label, i) => (
              <div key={i} className="empty-chip">
                <span className="empty-chip-dot" />
                {label}
              </div>
            ))}
          </div>
          <p className="empty-hint">Enter any URL above to begin analysis</p>
        </div>
      )}
    </div>
  )
}
