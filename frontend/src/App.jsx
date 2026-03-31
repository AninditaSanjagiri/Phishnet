import { useState } from 'react'
import Header from './components/Header.jsx'
import AnalyzerView from './components/AnalyzerView.jsx'
import HistoryView from './components/HistoryView.jsx'
import './App.css'

export default function App() {
  const [view, setView] = useState('analyzer')
  const [lastResult, setLastResult] = useState(null)

  return (
    <div className="app-shell">
      <Header activeView={view} onNavigate={setView} />
      <main className="app-main">
        {view === 'analyzer' && (
          <AnalyzerView onResult={setLastResult} lastResult={lastResult} />
        )}
        {view === 'history' && (
          <HistoryView />
        )}
      </main>
      <footer className="app-footer">
        <span className="mono" style={{ color: 'var(--text3)', fontSize: 12 }}>
          PhishNet v1.0 — Multimodal Phishing Detection &nbsp;|&nbsp; College Project
        </span>
      </footer>
    </div>
  )
}
