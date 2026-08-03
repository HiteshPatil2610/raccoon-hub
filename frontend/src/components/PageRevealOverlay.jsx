import { useEffect, useState } from 'react'
import './PageRevealOverlay.css'

const ROWS = 13
const COLS = 25
const CENTER_R = (ROWS - 1) / 2 // 6
const CENTER_C = (COLS - 1) / 2 // 12
const SPREAD_SECONDS = 1.8
const TILE_DURATION_SECONDS = 0.8
const REVEAL_START_DELAY_MS = 500
// Total time before the overlay is fully gone and removed from the DOM.
const TOTAL_LIFETIME_MS =
  REVEAL_START_DELAY_MS + (SPREAD_SECONDS + TILE_DURATION_SECONDS) * 1000 + 100

/**
 * Full-viewport, one-time intro curtain. Covers the entire app -
 * navbar included - as a single solid-color plane on mount, then
 * peels away tile-by-tile in an expanding square-ripple from the
 * center to reveal the real page underneath. Plays once per full
 * page load (mounted at the App root, not per-route), then unmounts
 * itself entirely so it isn't sitting in the DOM afterward.
 */
function getTileDelay(r, c) {
  const dx = c - CENTER_C
  const dy = r - CENTER_R

  // Euclidean distance (creates a circle)
  const dist = Math.sqrt(dx * dx + dy * dy)

  const maxDist = Math.sqrt(CENTER_C * CENTER_C + CENTER_R * CENTER_R)

  return (dist / maxDist) * SPREAD_SECONDS
}

export default function PageRevealOverlay() {
  const [isRevealed, setIsRevealed] = useState(false)
  const [isDone, setIsDone] = useState(false)

  useEffect(() => {
    const revealTimer = setTimeout(() => setIsRevealed(true), REVEAL_START_DELAY_MS)
    const doneTimer = setTimeout(() => setIsDone(true), TOTAL_LIFETIME_MS)
    return () => {
      clearTimeout(revealTimer)
      clearTimeout(doneTimer)
    }
  }, [])

  if (isDone) return null

  return (
    <div className={`page-reveal ${isRevealed ? 'is-revealed' : ''}`} aria-hidden="true">
      {Array.from({ length: ROWS }).map((_, r) =>
        Array.from({ length: COLS }).map((_, c) => (
          <div
            key={`${r}-${c}`}
            className="page-reveal__tile"
            style={{ transitionDelay: `${getTileDelay(r, c)}s` }}
          />
        ))
      )}
    </div>
  )
}