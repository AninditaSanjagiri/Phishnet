import { useState } from 'react'
import './URLInput.css'

const DEMO_URLS = [
  'https://google.com',
  'https://paypa1-secure-login.tk/verify',
  'https://github.com',
  'http://192.168.1.1/update-account',
]

export default function URLInput({ onSubmit, loading }) {
  const [url, setUrl] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (url.trim()) onSubmit(url.trim())
  }

  function loadDemo(demoUrl) {
    setUrl(demoUrl)
    onSubmit(demoUrl)
  }

  return (
    <div className="url-input-wrap">
      <form className="url-form" onSubmit={handleSubmit}>
        <div className={`url-field ${loading ? 'loading' : ''}`}>
          <span className="url-prefix mono">https://</span>
          <input
            className="url-input mono"
            type="text"
            placeholder="enter any URL to analyze..."
            value={url}
            onChange={e => setUrl(e.target.value)}
            disabled={loading}
            spellCheck={false}
            autoComplete="off"
          />
          <button
            className="url-submit"
            type="submit"
            disabled={loading || !url.trim()}
          >
            {loading ? (
              <span className="btn-spinner" />
            ) : (
              <>
                <span>Analyze</span>
                <span className="btn-arrow">→</span>
              </>
            )}
          </button>
        </div>
      </form>

      <div className="demo-row">
        <span className="demo-label">Try:</span>
        {DEMO_URLS.map((u, i) => (
          <button
            key={i}
            className="demo-btn mono"
            onClick={() => loadDemo(u)}
            disabled={loading}
          >
            {u.replace(/^https?:\/\//, '').slice(0, 36)}
          </button>
        ))}
      </div>
    </div>
  )
}
