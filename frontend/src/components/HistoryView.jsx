import { useState, useEffect } from 'react'
import { getHistory } from '../utils/api.js'
import './HistoryView.css'

function VerdictBadge({ verdict }) {
  const cfg = {
    phishing:   { color: 'danger', label: 'PHISHING' },
    suspicious: { color: 'warn',   label: 'SUSPICIOUS' },
    safe:       { color: 'safe',   label: 'SAFE' },
  }[verdict] || { color: 'text3', label: verdict?.toUpperCase() }

  return (
    <span className={`verdict-badge mono ${cfg.color}`}>{cfg.label}</span>
  )
}

function ScoreMini({ value, color }) {
  if (value === null || value === undefined) return <span className="mini-na mono">N/A</span>
  return (
    <div className="score-mini">
      <div className="score-mini-track">
        <div
          className={`score-mini-fill ${color}`}
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </div>
      <span className={`score-mini-label mono ${color}`}>
        {Math.round(value * 100)}%
      </span>
    </div>
  )
}

export default function HistoryView() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        const data = await getHistory(30)
        setRows(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="history-loading">
        <div className="history-spinner" />
        <span className="mono">Loading history…</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="history-error">
        <span>⚠ {error}</span>
      </div>
    )
  }

  if (rows.length === 0) {
    return (
      <div className="history-empty">
        <span className="mono">No analyses yet. Run the Analyzer to see history.</span>
      </div>
    )
  }

  return (
    <div className="history-view">
      <div className="history-header">
        <h2 className="history-title">Analysis History</h2>
        <span className="history-count mono">{rows.length} records</span>
      </div>

      <div className="history-table-wrap">
        <table className="history-table">
          <thead>
            <tr>
              <th className="mono">Time</th>
              <th className="mono">URL</th>
              <th className="mono">Verdict</th>
              <th className="mono">Overall</th>
              <th className="mono">URL</th>
              <th className="mono">Text</th>
              <th className="mono">Image</th>
              <th className="mono">Latency</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const verdict = row.verdict
              const scoreColor = row.phishing_probability >= 65 ? 'danger'
                               : row.phishing_probability >= 40 ? 'warn' : 'safe'
              return (
                <tr key={row.id} className={`history-row ${verdict}`}>
                  <td className="mono td-time">
                    {new Date(row.created_at).toLocaleTimeString([], {
                      hour: '2-digit', minute: '2-digit', second: '2-digit'
                    })}
                    <br />
                    <span className="td-date">
                      {new Date(row.created_at).toLocaleDateString()}
                    </span>
                  </td>
                  <td className="td-url">
                    <span className="url-text mono truncate">{row.url}</span>
                  </td>
                  <td><VerdictBadge verdict={verdict} /></td>
                  <td>
                    <span className={`mono score-overall ${scoreColor}`}>
                      {row.phishing_probability.toFixed(1)}%
                    </span>
                  </td>
                  <td><ScoreMini value={row.url_score}   color="accent" /></td>
                  <td><ScoreMini value={row.text_score}  color="purple" /></td>
                  <td><ScoreMini value={row.image_score} color="warn"   /></td>
                  <td className="mono td-latency">
                    {row.processing_time_ms != null
                      ? `${Math.round(row.processing_time_ms)}ms`
                      : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
