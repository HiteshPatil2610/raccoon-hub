import { useState } from 'react'
import './ImageGallery.css'

export default function ImageGallery({ mainImage, variants = [] }) {
  const images = [mainImage, ...variants].filter(Boolean)
  const [activeIndex, setActiveIndex] = useState(0)

  if (images.length === 0) {
    return <div className="image-gallery image-gallery--empty">No image available</div>
  }

  return (
    <div className="image-gallery">
      <div className="image-gallery__main">
        <img src={images[activeIndex]} alt="Product" />
      </div>
      {images.length > 1 && (
        <div className="image-gallery__thumbs">
          {images.map((src, i) => (
            <button
              key={src + i}
              type="button"
              className={`image-gallery__thumb ${i === activeIndex ? 'is-active' : ''}`}
              onClick={() => setActiveIndex(i)}
              aria-label={`View image ${i + 1}`}
            >
              <img src={src} alt="" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}