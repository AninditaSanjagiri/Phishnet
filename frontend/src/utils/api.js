import axios from 'axios'

// In dev, Vite proxies /api → localhost:8000
// In prod, set VITE_API_BASE to your Render backend URL
const BASE = import.meta.env.VITE_API_BASE || '/api'

const client = axios.create({
  baseURL: BASE,
  timeout: 60_000,   // 60s — screenshot capture can be slow
})

/**
 * Analyze a URL through the multimodal pipeline.
 * @param {string} url
 * @returns {Promise<AnalyzeResponse>}
 */
export async function analyzeUrl(url) {
  try {
    const { data } = await client.post('/analyze', { url })
    return data
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Request failed'
    throw new Error(msg)
  }
}

/**
 * Get recent analysis history.
 * @param {number} limit
 */
export async function getHistory(limit = 20) {
  try {
    const { data } = await client.get('/history', { params: { limit } })
    return data
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Failed to load history'
    throw new Error(msg)
  }
}

/**
 * Check if the backend is healthy.
 */
export async function checkHealth() {
  try {
    const { data } = await client.get('/health')
    return data.status === 'ok'
  } catch {
    return false
  }
}
