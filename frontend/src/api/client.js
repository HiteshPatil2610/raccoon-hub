/**
 * api/client.js
 * ------------------------------------------------------------------
 * Thin fetch wrapper around the backend API. Admin auth is a Bearer
 * token stored in localStorage and attached to every request via the
 * Authorization header - not a cookie. This was a deliberate switch
 * away from cookie-based sessions, since the frontend and backend
 * live on different subdomains in production and modern browsers
 * increasingly block third-party cookies in that exact cross-site
 * setup (Safari ITP by default, Chrome moving the same direction).
 * ------------------------------------------------------------------
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const TOKEN_STORAGE_KEY = 'raccoon_hub_admin_token'

function getToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
  }
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${path}`, {
    headers,
    ...options,
  })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      // response wasn't JSON - keep statusText
    }
    // A 401 always means "not currently authenticated" - clear any stale
    // token so the UI can fall back to the login screen cleanly.
    if (res.status === 401) {
      setToken(null)
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }

  if (res.status === 204) return null
  return res.json()
}

export const api = {
  // --- Admin ---
  login: async (password) => {
    const result = await request('/admin/login', {
      method: 'POST',
      body: JSON.stringify({ password }),
    })
    setToken(result.token)
    return result
  },
  logout: () => {
    setToken(null)
  },
  isLoggedIn: () => Boolean(getToken()),
  previewProduct: (url) =>
    request('/admin/products/preview', { method: 'POST', body: JSON.stringify({ url }) }),
  confirmProduct: (product, final_tags) =>
    request('/admin/products/confirm', {
      method: 'POST',
      body: JSON.stringify({ product, final_tags }),
    }),
  listAdminProducts: () => request('/admin/products'),
  updateProduct: (id, payload) =>
    request(`/admin/products/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteProduct: (id) => request(`/admin/products/${id}`, { method: 'DELETE' }),

  // --- Public ---
  listProducts: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/products${qs ? `?${qs}` : ''}`)
  },
  countProducts: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/products/count${qs ? `?${qs}` : ''}`)
  },
  getProduct: (asin) => request(`/products/${asin}`),
  getPriceHistory: (asin) => request(`/products/${asin}/price-history`),
  getSimilarProducts: (asin) => request(`/products/${asin}/similar`),
  listTags: () => request('/tags'),

  // --- Analytics (public click tracking) ---
  trackClick: (asin) =>
    request(`/admin/products/${asin}/track-click`, { method: 'POST' }).catch(() => {}),

  // --- Admin analytics ---
  getAnalytics: () => request('/admin/analytics'),

  // --- Bulk import ---
  bulkPreviewProducts: (urls) =>
    request('/admin/products/bulk-preview', {
      method: 'POST',
      body: JSON.stringify({ urls }),
    }),
}