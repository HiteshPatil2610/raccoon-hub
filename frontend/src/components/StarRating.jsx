/**
 * Renders nothing if no rating is present - which is always true right
 * now, since neither PA-API nor Creators API expose star ratings. This
 * component is ready for the day a manual-entry admin field (or a
 * future data source) provides `rating`/`count`, with zero changes
 * needed elsewhere.
 */
export default function StarRating({ rating, count }) {
  if (rating == null) return null

  const full = Math.round(rating)

  return (
    <div className="star-rating" aria-label={`${rating} out of 5 stars`}>
      <span>{'★'.repeat(full)}{'☆'.repeat(5 - full)}</span>
      {count != null && <span className="star-rating__count">({count})</span>}
    </div>
  )
}