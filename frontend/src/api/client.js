/**
 * api/client.js
 * ------------------------------------------------------------------
 * Thin fetch wrapper around the backend API. `credentials: 'include'`
 * is required on every call so the admin session cookie is sent -
 * without it, /admin/* routes will always 401 even after logging in.
 * ------------------------------------------------------------------
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
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
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }

  if (res.status === 204) return null
  return res.json()
}

export const api = {
  // --- Admin ---
  login: (password) =>
    request('/admin/login', { method: 'POST', body: JSON.stringify({ password }) }),
  logout: () => request('/admin/logout', { method: 'POST' }),
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
  getProduct: (asin) => request(`/products/${asin}`),
  listTags: () => request('/tags'),
}