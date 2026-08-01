import { useEffect, useState } from 'react'
import ProductCard from '../components/ProductCard.jsx'
import { api } from '../api/client.js'
import './Home.css'

export default function Home() {
  const [products, setProducts] = useState([])
  const [tags, setTags] = useState([])
  const [activeTag, setActiveTag] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.listTags().then(setTags).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    setError('')
    const params = activeTag ? { tag: activeTag } : {}
    api
      .listProducts(params)
      .then(setProducts)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [activeTag])

  return (
    <div className="home">
      <div className="home__header">
        <h1>Raccoon Hub</h1>
        <p>Hand-picked gear, straight to Amazon.</p>
      </div>

      {tags.length > 0 && (
        <div className="home__filters">
          <button className={activeTag === '' ? 'is-active' : ''} onClick={() => setActiveTag('')}>
            All
          </button>
          {tags.map((t) => (
            <button
              key={t.name}
              className={activeTag === t.name ? 'is-active' : ''}
              onClick={() => setActiveTag(t.name)}
            >
              {t.name}
            </button>
          ))}
        </div>
      )}

      {loading && <p className="home__status">Loading products…</p>}
      {error && <p className="home__status home__status--error">{error}</p>}
      {!loading && !error && products.length === 0 && (
        <p className="home__status">No products yet. Check back soon.</p>
      )}

      <div className="home__grid">
        {products.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </div>
  )
}