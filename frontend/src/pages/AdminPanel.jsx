import { useEffect, useState } from 'react'
import { api } from '../api/client.js'
import TagChipEditor from '../components/TagChipEditor.jsx'
import './AdminPanel.css'

export default function AdminPanel() {
  const [authed, setAuthed] = useState(() => api.isLoggedIn())
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')

  const [url, setUrl] = useState('')
  const [preview, setPreview] = useState(null) // { product, suggested_tags }
  const [tags, setTags] = useState([])
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState('')
  const [saveStatus, setSaveStatus] = useState('')

  const [products, setProducts] = useState([])

  const refreshProducts = () => {
    api
      .listAdminProducts()
      .then(setProducts)
      .catch(() => setAuthed(api.isLoggedIn())) // token may have just been cleared by a 401
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

  const handleToggleActive = async (product) => {
    await api.updateProduct(product.id, { is_active: !product.is_active })
    refreshProducts()
  }

  const handleDelete = async (product) => {
    if (!window.confirm(`Delete "${product.title}"? This can't be undone.`)) return
    await api.deleteProduct(product.id)
    refreshProducts()
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
              <p>
                {preview.product.price_display} &middot; {preview.product.availability}
              </p>
              <TagChipEditor tags={tags} onChange={setTags} />
              <button className="admin-panel__confirm" onClick={handleConfirm}>
                Confirm &amp; Add Product
              </button>
              {saveStatus && <p className="admin-panel__save-status">{saveStatus}</p>}
            </div>
          </div>
        )}
      </section>

      <section className="admin-panel__list">
        <h2>Existing products ({products.length})</h2>
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Price</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id}>
                <td>{p.title}</td>
                <td>{p.price_display}</td>
                <td>
                  <button onClick={() => handleToggleActive(p)}>
                    {p.is_active ? 'Active' : 'Hidden'}
                  </button>
                </td>
                <td>
                  <button onClick={() => handleDelete(p)} className="admin-panel__delete">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}