import { useEffect, useState } from 'react'
import { api } from '../api/client.js'
import TagChipEditor from '../components/TagChipEditor.jsx'
import './AdminPanel.css'

// ---------------------------------------------------------------------------
// ProductRow — single row in the products table with inline tag editing
// ---------------------------------------------------------------------------
function ProductRow({ product, onRefresh }) {
  const [editingTags, setEditingTags] = useState(false)
  const [tags, setTags] = useState(product.tags || [])
  const [saving, setSaving] = useState(false)

  const handleToggleActive = async () => {
    await api.updateProduct(product.id, { is_active: !product.is_active })
    onRefresh()
  }

  const handleDelete = async () => {
    if (!window.confirm(`Delete "${product.title}"? This can't be undone.`)) return
    await api.deleteProduct(product.id)
    onRefresh()
  }

  const handleSaveTags = async () => {
    setSaving(true)
    try {
      await api.updateProduct(product.id, { tags })
      setEditingTags(false)
      onRefresh()
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <tr>
        <td>{product.title}</td>
        <td>{product.price_display}</td>
        <td>
          <button onClick={handleToggleActive}>
            {product.is_active ? 'Active' : 'Hidden'}
          </button>
        </td>
        <td>
          <button
            className="admin-panel__edit-tags"
            onClick={() => setEditingTags((v) => !v)}
          >
            Tags ({(product.tags || []).length})
          </button>
        </td>
        <td>
          <button onClick={handleDelete} className="admin-panel__delete">Delete</button>
        </td>
      </tr>
      {editingTags && (
        <tr className="admin-panel__tag-edit-row">
          <td colSpan={5}>
            <div className="admin-panel__tag-edit">
              <TagChipEditor tags={tags} onChange={setTags} />
              <div className="admin-panel__tag-edit-actions">
                <button className="admin-panel__tag-save" onClick={handleSaveTags} disabled={saving}>
                  {saving ? 'Saving…' : 'Save tags'}
                </button>
                <button className="admin-panel__tag-cancel" onClick={() => { setTags(product.tags || []); setEditingTags(false) }}>
                  Cancel
                </button>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

// ---------------------------------------------------------------------------
// BulkImport — paste or upload a list of Amazon URLs
// ---------------------------------------------------------------------------
function BulkImport() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const urls = text.split('\n').map((u) => u.trim()).filter(Boolean)
    if (!urls.length) return
    setLoading(true)
    setResults(null)
    try {
      const res = await api.bulkPreviewProducts(urls)
      setResults(res)
    } catch (err) {
      setResults([{ url: 'Request failed', success: false, error: err.message }])
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      const content = ev.target.result
      // Support CSV with a "url" column or plain one-per-line
      const lines = content.split('\n').map((l) => l.trim()).filter(Boolean)
      const urls = lines
        .map((l) => {
          // If it looks like a CSV header or quoted field, strip quotes
          const col = l.split(',')[0].replace(/^"|"$/g, '').trim()
          return col.toLowerCase() === 'url' ? null : col
        })
        .filter(Boolean)
      setText(urls.join('\n'))
    }
    reader.readAsText(file)
  }

  return (
    <section className="admin-panel__bulk">
      <h2>Bulk import</h2>
      <p className="admin-panel__bulk-hint">
        Paste Amazon URLs (one per line) or upload a CSV with a <code>url</code> column.
        Max 20 URLs per batch.
      </p>
      <form onSubmit={handleSubmit} className="admin-panel__bulk-form">
        <textarea
          rows={6}
          placeholder="https://www.amazon.in/dp/B0XXXXXXXXXX&#10;https://www.amazon.in/dp/B0YYYYYYYYYY"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="admin-panel__bulk-controls">
          <label className="admin-panel__bulk-upload">
            Upload CSV
            <input type="file" accept=".csv,.txt" onChange={handleFileUpload} hidden />
          </label>
          <button type="submit" disabled={loading || !text.trim()}>
            {loading ? 'Previewing…' : 'Preview all'}
          </button>
        </div>
      </form>

      {results && (
        <div className="admin-panel__bulk-results">
          <p className="admin-panel__bulk-summary">
            {results.filter((r) => r.success).length} succeeded ·{' '}
            {results.filter((r) => !r.success).length} failed
          </p>
          {results.map((r, i) => (
            <div
              key={i}
              className={`admin-panel__bulk-item ${r.success ? 'is-success' : 'is-error'}`}
            >
              {r.success ? (
                <>
                  <span className="admin-panel__bulk-status">✓</span>
                  <span className="admin-panel__bulk-title">{r.product?.title || r.url}</span>
                  <span className="admin-panel__bulk-price">{r.product?.price_display}</span>
                </>
              ) : (
                <>
                  <span className="admin-panel__bulk-status">✗</span>
                  <span className="admin-panel__bulk-url">{r.url}</span>
                  <span className="admin-panel__bulk-error">{r.error}</span>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Analytics — top products by views + clicks
// ---------------------------------------------------------------------------
function Analytics() {
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getAnalytics()
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="admin-panel__analytics-loading">Loading analytics…</p>
  if (!stats.length) return <p className="admin-panel__analytics-loading">No data yet.</p>

  return (
    <section className="admin-panel__analytics">
      <h2>Analytics</h2>
      <table>
        <thead>
          <tr>
            <th>Product</th>
            <th>Views</th>
            <th>Clicks</th>
          </tr>
        </thead>
        <tbody>
          {stats.map((p) => (
            <tr key={p.asin}>
              <td className="admin-panel__analytics-title">{p.title || p.asin}</td>
              <td>{p.view_count ?? 0}</td>
              <td>{p.click_count ?? 0}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

// ---------------------------------------------------------------------------
// AdminPanel — main page
// ---------------------------------------------------------------------------
export default function AdminPanel() {
  const [authed, setAuthed] = useState(() => api.isLoggedIn())
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')

  const [url, setUrl] = useState('')
  const [preview, setPreview] = useState(null)
  const [tags, setTags] = useState([])
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState('')
  const [saveStatus, setSaveStatus] = useState('')

  const [products, setProducts] = useState([])

  const refreshProducts = () => {
    api.listAdminProducts()
      .then(setProducts)
      .catch(() => setAuthed(api.isLoggedIn()))
  }

  useEffect(() => {
    if (authed) refreshProducts()
  }, [authed])

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoginError('')
    try {
      await api.login(password)
      setAuthed(true)
    } catch (err) {
      setLoginError(err.message || 'Login failed.')
    }
  }

  const handlePreview = async (e) => {
    e.preventDefault()
    setPreviewError('')
    setPreview(null)
    setSaveStatus('')
    setPreviewLoading(true)
    try {
      const result = await api.previewProduct(url)
      setPreview(result)
      setTags(result.suggested_tags)
    } catch (err) {
      setPreviewError(err.message)
      setAuthed(api.isLoggedIn())
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleConfirm = async () => {
    if (!preview) return
    setSaveStatus('Saving…')
    try {
      await api.confirmProduct(preview.product, tags)
      setSaveStatus('Saved!')
      setPreview(null)
      setUrl('')
      setTags([])
      refreshProducts()
    } catch (err) {
      setSaveStatus(`Error: ${err.message}`)
      setAuthed(api.isLoggedIn())
    }
  }

  if (!authed) {
    return (
      <div className="admin-login">
        <form onSubmit={handleLogin}>
          <h1>Admin Login</h1>
          <input
            type="password"
            placeholder="Admin password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
          />
          <button type="submit">Log in</button>
          {loginError && <p className="admin-login__error">{loginError}</p>}
        </form>
      </div>
    )
  }

  return (
    <div className="admin-panel">
      <h1>Admin Panel</h1>

      {/* ---- Single product add ---- */}
      <section className="admin-panel__add">
        <h2>Add a product</h2>
        <form onSubmit={handlePreview} className="admin-panel__add-form">
          <input
            type="text"
            placeholder="Paste any Amazon.in product link"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <button type="submit" disabled={previewLoading || !url}>
            {previewLoading ? 'Fetching…' : 'Preview'}
          </button>
        </form>
        {previewError && <p className="admin-panel__error">{previewError}</p>}

        {preview && (
          <div className="admin-panel__preview">
            <img src={preview.product.image_large_url} alt={preview.product.title} />
            <div className="admin-panel__preview-info">
              <h3>{preview.product.title}</h3>
              <p>{preview.product.price_display} &middot; {preview.product.availability}</p>
              {preview.product.ai_blurb && (
                <p className="admin-panel__blurb">✨ {preview.product.ai_blurb}</p>
              )}
              <TagChipEditor tags={tags} onChange={setTags} />
              <button className="admin-panel__confirm" onClick={handleConfirm}>
                Confirm &amp; Add Product
              </button>
              {saveStatus && <p className="admin-panel__save-status">{saveStatus}</p>}
            </div>
          </div>
        )}
      </section>

      {/* ---- Bulk import ---- */}
      <BulkImport />

      {/* ---- Existing products ---- */}
      <section className="admin-panel__list">
        <h2>Existing products ({products.length})</h2>
        <table>
          <thead>
            <tr>
              <th>Title</th><th>Price</th><th>Status</th><th>Tags</th><th></th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <ProductRow key={p.id} product={p} onRefresh={refreshProducts} />
            ))}
          </tbody>
        </table>
      </section>

      {/* ---- Analytics ---- */}
      <Analytics />
    </div>
  )
}
