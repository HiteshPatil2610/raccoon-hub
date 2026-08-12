import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import ImageGallery from '../components/ImageGallery.jsx'
import BuyButton from '../components/BuyButton.jsx'
import StarRating from '../components/StarRating.jsx'
import PriceSparkline from '../components/PriceSparkline.jsx'
import { api } from '../api/client.js'
import './ProductDetail.css'
import '../components/PriceSparkline.css'

// ---- SEO helpers -------------------------------------------------------
function setMeta(property, content) {
  let el = document.querySelector(`meta[property="${property}"]`)
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute('property', property)
    document.head.appendChild(el)
  }
  el.setAttribute('content', content || '')
}

function applyProductSEO(product) {
  const title = product.title ? `${product.title} — Raccoon Hub` : 'Raccoon Hub'
  const description = product.ai_blurb || product.price_display || 'View this product on Raccoon Hub.'
  const image = product.image_large_url || ''
  const url = window.location.href

  document.title = title
  setMeta('og:title', title)
  setMeta('og:description', description)
  setMeta('og:image', image)
  setMeta('og:url', url)
  setMeta('og:type', 'product')
}

function resetSEO() {
  document.title = 'Raccoon Hub'
}
// ------------------------------------------------------------------------

export default function ProductDetail() {
  const { asin } = useParams()
  const [product, setProduct] = useState(null)
  const [priceHistory, setPriceHistory] = useState([])
  const [similar, setSimilar] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    setPriceHistory([])
    setSimilar([])

    api
      .getProduct(asin)
      .then((p) => {
        setProduct(p)
        applyProductSEO(p)

        // Fetch price history + similar products in parallel (non-blocking)
        api.getPriceHistory(asin).then(setPriceHistory).catch(() => {})
        api.getSimilarProducts(asin).then(setSimilar).catch(() => {})
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))

    // Reset title/meta when leaving the page
    return () => resetSEO()
  }, [asin])

  if (loading) return <p className="product-detail__status">Loading…</p>
  if (error) return <p className="product-detail__status product-detail__status--error">{error}</p>
  if (!product) return null

  const inStock =
    (product.availability || '').toLowerCase().includes('stock') &&
    !(product.availability || '').toLowerCase().includes('out of')

  return (
    <div className="product-detail">
      <Link to="/" className="product-detail__back">
        &larr; Back to all products
      </Link>

      <div className="product-detail__layout">
        <ImageGallery mainImage={product.image_large_url} variants={product.image_variants} />

        <div className="product-detail__info">
          <h1>{product.title}</h1>
          <StarRating rating={product.star_rating} count={product.review_count} />
          <div className="product-detail__price">{product.price_display}</div>
          <div
            className={`product-detail__availability product-detail__availability--${inStock ? 'in' : 'out'}`}
          >
            {product.availability}
          </div>

          {product.tags?.length > 0 && (
            <div className="product-detail__tags">
              {product.tags.map((t) => (
                <span key={t.name} className={`tag-chip tag-chip--${t.tag_type}`}>
                  {t.name}
                </span>
              ))}
            </div>
          )}

          {product.ai_blurb && <p className="product-detail__blurb">{product.ai_blurb}</p>}

          {/* Price sparkline — only shown when ≥2 history points exist */}
          <PriceSparkline history={priceHistory} />

          {product.features?.length > 0 && (
            <ul className="product-detail__features">
              {product.features.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          )}

          <BuyButton asin={product.asin} />
        </div>
      </div>

      {/* Similar products row */}
      {similar.length > 0 && (
        <section className="product-detail__similar">
          <h2 className="product-detail__similar-heading">Similar products</h2>
          <div className="product-detail__similar-grid">
            {similar.map((p) => (
              <Link
                key={p.asin}
                to={`/product/${p.asin}`}
                className="product-detail__similar-card"
              >
                {p.image_large_url && (
                  <img src={p.image_large_url} alt={p.title || 'Product'} loading="lazy" />
                )}
                <div className="product-detail__similar-info">
                  <p className="product-detail__similar-title">{p.title}</p>
                  <p className="product-detail__similar-price">{p.price_display}</p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
