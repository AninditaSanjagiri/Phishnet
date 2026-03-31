import './LoadingState.css'

const STEPS = [
  { icon: '🔗', label: 'Extracting URL features…' },
  { icon: '📄', label: 'Fetching & classifying page content…' },
  { icon: '🖼', label: 'Capturing screenshot…' },
  { icon: '🔀', label: 'Fusing agent signals…' },
]

export default function LoadingState() {
  return (
    <div className="loading-state">
      <div className="loading-header">
        <div className="loading-scanner">
          <div className="scanner-ring" />
          <div className="scanner-dot" />
        </div>
        <span className="loading-title mono">Scanning URL…</span>
      </div>

      <div className="loading-steps">
        {STEPS.map((step, i) => (
          <div
            key={i}
            className="loading-step"
            style={{ animationDelay: `${i * 0.18}s` }}
          >
            <span className="step-icon">{step.icon}</span>
            <span className="step-bar">
              <span className="step-fill" style={{ animationDelay: `${i * 0.18 + 0.1}s` }} />
            </span>
            <span className="step-label mono">{step.label}</span>
          </div>
        ))}
      </div>

      <p className="loading-note mono">
        All agents run in parallel · typically 1–3 seconds
      </p>
    </div>
  )
}
