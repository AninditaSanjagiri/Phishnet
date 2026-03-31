import { useState } from 'react'
import './AgentCard.css'

function ScoreBar({ value, color }) {
  if (value === null || value === undefined) {
    return <div className="score-bar-wrap"><div className="score-bar-na mono">N/A</div></div>
  }
  const pct = Math.round(value * 100)
  return (
    <div className="score-bar-wrap">
      <div className="score-bar-track">
        <div
          className={`score-bar-fill ${color}`}
          style={{ width: `${pct}%`, animation: 'bar-fill 0.8s cubic-bezier(0.4,0,0.2,1)' }}
        />
      </div>
      <span className={`score-bar-label mono ${color}`}>{pct}%</span>
    </div>
  )
}

const COLOR_VAR = { accent: '--accent', purple: '--purple', warn: '--warn' }

export default function AgentCard({ title, subtitle, icon, agentResult, color }) {
  const [expanded, setExpanded] = useState(false)
  const score = agentResult?.score
  const confidence = agentResult?.confidence ?? 0
  const explanation = agentResult?.explanation ?? 'No data'
  const features = agentResult?.features ?? {}

  const unavailable = score === null || score === undefined

  return (
    <div className={`agent-card ${color} ${unavailable ? 'unavailable' : ''}`}>
      <div className="card-header">
        <div className="card-icon">{icon}</div>
        <div className="card-titles">
          <span className="card-title">{title}</span>
          <span className="card-sub mono">{subtitle}</span>
        </div>
        <div className={`card-verdict-dot ${unavailable ? 'na' : score > 0.5 ? 'danger' : score > 0.3 ? 'warn' : 'safe'}`} />
      </div>

      <div className="card-score-section">
        <div className="score-row">
          <span className="score-meta mono">Phishing probability</span>
        </div>
        <ScoreBar value={score} color={score > 0.5 ? 'danger' : score > 0.3 ? 'warn' : 'safe'} />

        <div className="score-row" style={{ marginTop: 8 }}>
          <span className="score-meta mono">Confidence</span>
        </div>
        <ScoreBar value={confidence} color={color} />
      </div>

      <div className="card-explanation">{explanation}</div>

      {Object.keys(features).length > 0 && (
        <button
          className="card-expand-btn mono"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? '▲ hide features' : '▼ show features'}
        </button>
      )}

      {expanded && (
        <div className="card-features">
          {Object.entries(features).map(([k, v]) => {
            if (k === 'top_tokens' && Array.isArray(v)) {
              return (
                <div key={k} className="feature-row">
                  <span className="feat-key mono">{k}</span>
                  <span className="feat-val mono">{v.join(', ') || '—'}</span>
                </div>
              )
            }
            if (typeof v === 'object') return null
            return (
              <div key={k} className="feature-row">
                <span className="feat-key mono">{k}</span>
                <span className="feat-val mono">{String(v)}</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
