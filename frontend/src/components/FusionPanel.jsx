import './FusionPanel.css'

export default function FusionPanel({ result }) {
  const weights = result.fusion_weights || {}
  const agents = [
    { key: 'url',   label: 'URL',   score: result.url_agent?.score,   color: 'accent' },
    { key: 'text',  label: 'Text',  score: result.text_agent?.score,  color: 'purple' },
    { key: 'image', label: 'Image', score: result.image_agent?.score, color: 'warn'   },
  ]

  return (
    <div className="fusion-panel">
      <div className="panel-header">
        <span className="panel-title">Fusion Layer</span>
        <span className="panel-method mono">{weights.method || 'weighted avg'}</span>
      </div>

      <div className="fusion-agents">
        {agents.map(({ key, label, score, color }) => {
          const w = weights[key]
          const available = score !== null && score !== undefined
          return (
            <div key={key} className={`fusion-row ${!available ? 'na' : ''}`}>
              <span className={`fusion-agent-label mono ${color}`}>{label}</span>

              <div className="fusion-bar-track">
                <div
                  className={`fusion-bar-fill ${color}`}
                  style={{
                    width: available ? `${Math.round(score * 100)}%` : '0%',
                    animation: 'bar-fill 0.9s cubic-bezier(0.4,0,0.2,1)',
                  }}
                />
              </div>

              <span className="fusion-score mono">
                {available ? `${Math.round(score * 100)}%` : 'N/A'}
              </span>

              {w !== undefined && w !== 'method' && (
                <span className="fusion-weight mono">×{Number(w).toFixed(2)}</span>
              )}
            </div>
          )
        })}
      </div>

      <div className="fusion-final">
        <span className="fusion-final-label mono">Final phishing probability</span>
        <span
          className="fusion-final-score mono"
          style={{
            color: result.phishing_probability >= 65 ? 'var(--danger)'
                 : result.phishing_probability >= 40 ? 'var(--warn)'
                 : 'var(--safe)',
          }}
        >
          {result.phishing_probability}%
        </span>
      </div>

      <div className="threshold-guide">
        <div className="tg-item">
          <span className="tg-dot safe" />
          <span className="mono">&lt;40% safe</span>
        </div>
        <div className="tg-item">
          <span className="tg-dot warn" />
          <span className="mono">40–65% suspicious</span>
        </div>
        <div className="tg-item">
          <span className="tg-dot danger" />
          <span className="mono">&gt;65% phishing</span>
        </div>
      </div>
    </div>
  )
}
