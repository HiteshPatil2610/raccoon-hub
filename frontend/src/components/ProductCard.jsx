import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Heart, Sparkles, Star } from 'lucide-react'
import './ProductCard.css'

const FAVORITES_KEY = 'raccoon_hub_favorites'

function getFavorites() {
  try {
    return new Set(JSON.parse(localStorage.getItem(FAVORITES_KEY) || '[]'))
  } catch {
    return new Set()
  }
}

function saveFavorites(set) {
  localStorage.setItem(FAVORITES_KEY, JSON.stringify([...set]))
}

export default function ProductCard({ product }) {
  const [isLiked, setIsLiked] = useState(() => getFavorites().has(product.asin))
  const [burst, setBurst] = useState(false)

  const toggleLike = (e) => {
    e.preventDefault() // don't navigate when clicking the heart
    e.stopPropagation()

    const favorites = getFavorites()
    const nextLiked = !isLiked
    if (nextLiked) {
      favorites.add(product.asin)
      setBurst(true)
      setTimeout(() => setBurst(false), 700)
    } else {
      favorites.delete(product.asin)
    }
    saveFavorites(favorites)
    setIsLiked(nextLiked)
  }

  return (
    <Link to={`/product/${product.asin}`} className="product-card">
      {/* Radial "liked" burst, matches the reference design's like animation */}
      <div className="product-card__burst-anchor">
        {burst && <div className="product-card__burst" />}
      </div>

      <button
        type="button"
        className="product-card__like"
        onClick={toggleLike}
        title={isLiked ? 'Remove from favorites' : 'Save to favorites'}
      >
        <Heart className={`product-card__like-icon ${isLiked ? 'is-liked' : ''}`} />
      </button>

      <div className="product-card__image-wrap">
        {product.image_large_url ? (
          <img src={product.image_large_url} alt={product.title || 'Product'} loading="lazy" />
        ) : (
          <div className="product-card__image-placeholder">No image</div>
        )}
      </div>

      {/* Gradient + blur reveal panel - fades in on hover */}
      <div className="product-card__overlay" />

      <div className="product-card__info">
        <div className="product-card__top-row">
          <h3 className="product-card__title">{product.title || 'Untitled product'}</h3>
          <span className="product-card__price">{product.price_display || '—'}</span>
        </div>

        <div className="product-card__meta">
          {product.star_rating != null && (
            <span className="product-card__rating">
              <Star className="product-card__rating-icon" />
              {product.star_rating}
            </span>
          )}
          {product.category && <span className="product-card__category">{product.category}</span>}
        </div>

        <div className="product-card__hint">
          <Sparkles className="product-card__hint-icon" />
          View details
        </div>
      </div>
    </Link>
  )
}