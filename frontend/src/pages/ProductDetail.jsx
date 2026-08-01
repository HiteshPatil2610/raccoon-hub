import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import ImageGallery from '../components/ImageGallery.jsx'
import BuyButton from '../components/BuyButton.jsx'
import StarRating from '../components/StarRating.jsx'
import { api } from '../api/client.js'
import './ProductDetail.css'

export default function ProductDetail() {
  const { asin } = useParams()
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    api
      .getProduct(asin)
      .then(setProduct)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [asin])

  if (loading) return <p className="product-detail__status">Loading…</p>
  if (error) return <p className="product-detail__status product-detail__status--error">{error}</p>
  if (!product) return null

  const inStock = (product.availability || '').toLowerCase().includes('stock') &&
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
    </div>
  )
}