import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'motion/react'
import { Heart, Sparkles, Star, X, ChevronRight } from 'lucide-react'
import ImageGallery from './ImageGallery.jsx'
import BuyButton from './BuyButton.jsx'
import StarRating from './StarRating.jsx'
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

export default function ProductCard({ product, isExpanded, onToggleExpand }) {
  const [isLiked, setIsLiked] = useState(() => getFavorites().has(product.asin))
  const [burst, setBurst] = useState(false)
  const [isShrinking, setIsShrinking] = useState(false)
  const prevExpandedRef = useRef(isExpanded)

  // Briefly keep the shrinking card above its neighbors so it doesn't
  // visually clip beneath them mid-collapse (matches the reference design).
  useEffect(() => {
    if (prevExpandedRef.current && !isExpanded) {
      setIsShrinking(true)
      const timer = setTimeout(() => setIsShrinking(false), 700)
      return () => clearTimeout(timer)
    }
    prevExpandedRef.current = isExpanded
  }, [isExpanded])

  const toggleLike = (e) => {
    e.preventDefault()
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

  const availStr = (product.availability || '').toLowerCase()
  const inStock = availStr.includes('stock') && !availStr.includes('out of')
  const isOutOfStock = availStr.includes('out of stock') || availStr === 'out of stock'

  return (
    <motion.div
      layout
      transition={{ layout: { type: 'spring', stiffness: 280, damping: 30 } }}
      onClick={() => {
        if (!isExpanded) onToggleExpand()
      }}
      className={`product-card ${
        isExpanded ? 'is-expanded' : isShrinking ? 'is-shrinking' : ''
      }${isOutOfStock ? ' is-out-of-stock' : ''}`}
    >
      <div className="product-card__sheen" />

      <AnimatePresence mode="popLayout" initial={false}>
        {isExpanded ? (
          /* ============================ EXPANDED ============================ */
          <motion.div
            key="expanded"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25, delay: 0.15, ease: 'easeOut' }}
            className="product-card__expanded"
          >
            <div className="product-card__expanded-header">
              <nav className="product-card__breadcrumb">
                <span>Shop</span>
                {product.category && (
                  <>
                    <ChevronRight className="product-card__breadcrumb-icon" />
                    <span>{product.category}</span>
                  </>
                )}
                <ChevronRight className="product-card__breadcrumb-icon" />
                <span className="product-card__breadcrumb-current">{product.title}</span>
              </nav>
              <button
                type="button"
                className="product-card__close"
                onClick={(e) => {
                  e.stopPropagation()
                  onToggleExpand()
                }}
              >
                <X className="product-card__close-icon" />
                Close
              </button>
            </div>

            <div className="product-card__expanded-body">
              <div className="product-card__gallery-col" onClick={(e) => e.stopPropagation()}>
                <ImageGallery mainImage={product.image_large_url} variants={product.image_variants} />
              </div>

              <div className="product-card__info-col">
                <h2 className="product-card__expanded-title">{product.title}</h2>
                <StarRating rating={product.star_rating} count={product.review_count} />
                <div className="product-card__expanded-price">{product.price_display}</div>
                <div
                  className={`product-card__availability ${
                    inStock ? 'product-card__availability--in' : 'product-card__availability--out'
                  }`}
                >
                  {product.availability}
                </div>

                {product.tags?.length > 0 && (
                  <div className="product-card__tags">
                    {product.tags.map((t) => (
                      <span key={t.name} className={`tag-chip tag-chip--${t.tag_type}`}>
                        {t.name}
                      </span>
                    ))}
                  </div>
                )}

                {product.ai_blurb && <p className="product-card__blurb">{product.ai_blurb}</p>}

                {product.features?.length > 0 && (
                  <ul className="product-card__features">
                    {product.features.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                )}

                <div className="product-card__expanded-actions" onClick={(e) => e.stopPropagation()}>
                  <BuyButton asin={product.asin} />
                  <Link to={`/product/${product.asin}`} className="product-card__full-page-link">
                    View full page &rarr;
                  </Link>
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          /* ============================ COLLAPSED ============================ */
          <motion.div
            key="collapsed"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25, delay: 0.15, ease: 'easeOut' }}
            className="product-card__collapsed"
          >
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

            {isOutOfStock && (
              <div className="product-card__oos-badge">Out of Stock</div>
            )}

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
                Click to expand
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}