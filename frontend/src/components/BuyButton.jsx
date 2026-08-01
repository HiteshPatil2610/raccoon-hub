import './BuyButton.css'

const ASSOCIATE_TAG = import.meta.env.VITE_AMAZON_ASSOCIATE_TAG || 'yourtag-21'

export default function BuyButton({ asin }) {
  const url = `https://www.amazon.in/dp/${asin}?tag=${ASSOCIATE_TAG}`

  return (
    <a className="buy-button" href={url} target="_blank" rel="noopener noreferrer sponsored">
      Buy on Amazon
    </a>
  )
}