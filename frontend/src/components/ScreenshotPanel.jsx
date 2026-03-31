import { useState } from 'react'
import './ScreenshotPanel.css'

export default function ScreenshotPanel({ result }) {
  const [showGradcam, setShowGradcam] = useState(false)

  const screenshotSrc = result.screenshot_base64
    ? `data:image/png;base64,${result.screenshot_base64}`
    : null
  const gradcamSrc = result.gradcam_base64
    ? `data:image/png;base64,${result.gradcam_base64}`
    : null

  const currentSrc = showGradcam && gradcamSrc ? gradcamSrc : screenshotSrc

  if (!screenshotSrc) return null

  return (
    <div className="screenshot-panel">
      <div className="panel-header">
        <span className="panel-title">Visual Analysis</span>
        {gradcamSrc && (
          <div className="gradcam-toggle">
            <button
              className={`toggle-btn mono ${!showGradcam ? 'active' : ''}`}
              onClick={() => setShowGradcam(false)}
            >
              Screenshot
            </button>
            <button
              className={`toggle-btn mono ${showGradcam ? 'active' : ''}`}
              onClick={() => setShowGradcam(true)}
            >
              GradCAM ▲
            </button>
          </div>
        )}
      </div>

      <div className="screenshot-wrap">
        <img
          src={currentSrc}
          alt={showGradcam ? 'GradCAM heatmap overlay' : 'Page screenshot'}
          className="screenshot-img"
        />
        {showGradcam && (
          <div className="gradcam-legend">
            <span className="legend-item">
              <span className="legend-swatch hot" /> High activation
            </span>
            <span className="legend-item">
              <span className="legend-swatch cold" /> Low activation
            </span>
          </div>
        )}
      </div>

      <div className="screenshot-caption mono">
        {showGradcam
          ? 'Red regions show where MobileNetV3 focused when classifying this page.'
          : 'Captured via headless Chromium · ' + new Date().toLocaleTimeString()}
      </div>
    </div>
  )
}
