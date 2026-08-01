import { Link } from 'react-router-dom'
import './ProductCard.css'

export default function ProductCard({ product }) {
  return (
    <Link to={`/product/${product.asin}`} className="product-card">
      <div className="product-card__image">
        {product.image_large_url ? (
          <img src={product.image_large_url} alt={product.title || 'Product'} loading="lazy" />
        ) : (
          <div className="product-card__image-placeholder">No image</div>
        )}
      </div>
      <div className="product-card__body">
        <h3 className="product-card__title">{product.title || 'Untitled product'}</h3>
        <div className="product-card__price">{product.price_display || 'Price unavailable'}</div>
        {product.category && <span className="product-card__category">{product.category}</span>}
      </div>
    </Link>
  )
}