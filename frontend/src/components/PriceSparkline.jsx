/**
 * PriceSparkline
 * ------------------------------------------------------------------
 * SVG sparkline showing price history for a product.
 * Receives an array of { price_amount, price_display, recorded_at }.
 * Shows min/max labels and a subtle trend line.
 * ------------------------------------------------------------------
 */
export default function PriceSparkline({ history }) {
  if (!history || history.length < 2) return null

  const prices = history.map((h) => Number(h.price_amount))
  const dates = history.map((h) => new Date(h.recorded_at))

  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  const priceRange = maxPrice - minPrice || 1

  const W = 280
  const H = 60
  const PAD = 4

  // Map each point to SVG coordinates
  const points = prices.map((p, i) => {
    const x = PAD + (i / (prices.length - 1)) * (W - PAD * 2)
    const y = PAD + ((maxPrice - p) / priceRange) * (H - PAD * 2)
    return [x, y]
  })

  const polyline = points.map(([x, y]) => `${x},${y}`).join(' ')

  // Fill path: polyline + down to bottom-right + bottom-left
  const fillPath =
    `M ${points[0][0]},${points[0][1]} ` +
    points.slice(1).map(([x, y]) => `L ${x},${y}`).join(' ') +
    ` L ${points[points.length - 1][0]},${H} L ${points[0][0]},${H} Z`

  const latestPrice = history[history.length - 1].price_display
  const trend = prices[prices.length - 1] <= prices[0] ? 'down' : 'up'

  // Format date nicely
  const fmt = (d) =>
    d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })

  return (
    <div className="price-sparkline">
      <div className="price-sparkline__header">
        <span className="price-sparkline__label">Price history</span>
        <span className={`price-sparkline__trend price-sparkline__trend--${trend}`}>
          {trend === 'down' ? '↓' : '↑'} {latestPrice}
        </span>
      </div>

      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="price-sparkline__svg"
        aria-hidden="true"
      >
        {/* Fill area */}
        <path d={fillPath} className="price-sparkline__fill" />
        {/* Line */}
        <polyline points={polyline} className="price-sparkline__line" />
        {/* Dots at first and last point */}
        <circle cx={points[0][0]} cy={points[0][1]} r="3" className="price-sparkline__dot" />
        <circle
          cx={points[points.length - 1][0]}
          cy={points[points.length - 1][1]}
          r="3"
          className="price-sparkline__dot price-sparkline__dot--latest"
        />
      </svg>

      <div className="price-sparkline__footer">
        <span className="price-sparkline__date">{fmt(dates[0])}</span>
        <span className="price-sparkline__range">
          ₹{minPrice.toLocaleString('en-IN')} – ₹{maxPrice.toLocaleString('en-IN')}
        </span>
        <span className="price-sparkline__date">{fmt(dates[dates.length - 1])}</span>
      </div>
    </div>
  )
}
