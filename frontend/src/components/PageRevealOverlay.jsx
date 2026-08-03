import { useEffect, useLayoutEffect, useState } from 'react'
import './PageRevealOverlay.css'

const COLS = 25
const SPREAD_SECONDS = 1.8
const TILE_DURATION_SECONDS = 0.8
const REVEAL_START_DELAY_MS = 500
const TOTAL_LIFETIME_MS =
  REVEAL_START_DELAY_MS + (SPREAD_SECONDS + TILE_DURATION_SECONDS) * 1000 + 100

/**
 * Full-viewport, one-time intro curtain. Covers the entire app -
 * navbar included - as a single solid-color plane on mount, then
 * peels away tile-by-tile in an expanding circular ripple from the
 * center to reveal the real page underneath.
 *
 * Grid sizing: columns are fixed at 25. Row count is *derived*, not
 * fixed, so tiles stay square on any screen size instead of stretching
 * into rectangles:
 *   1. tileWidth = viewport width / 25
 *   2. rows = round(viewport height / tileWidth)
 * This is computed once at mount via useLayoutEffect (runs before the
 * browser paints, so there's no visible flash of the wrong grid) - not
 * recalculated on window resize, since resizing mid-animation would
 * visibly jump the grid; it's a ~3 second intro, not a persistent layout.
 */
function getTileDelay(r, c, centerR, centerC, maxDist) {
  const dx = c - centerC
  const dy = r - centerR
  const dist = Math.sqrt(dx * dx + dy * dy)
  return (dist / maxDist) * SPREAD_SECONDS
}

export default function PageRevealOverlay() {
  const [rows, setRows] = useState(null)
  const [isRevealed, setIsRevealed] = useState(false)
  const [isDone, setIsDone] = useState(false)

  useLayoutEffect(() => {
    const tileWidth = window.innerWidth / COLS
    const computedRows = Math.max(1, Math.round(window.innerHeight / tileWidth))
    setRows(computedRows)
  }, [])

  useEffect(() => {
    if (rows == null) return
    const revealTimer = setTimeout(() => setIsRevealed(true), REVEAL_START_DELAY_MS)
    const doneTimer = setTimeout(() => setIsDone(true), TOTAL_LIFETIME_MS)
    return () => {
      clearTimeout(revealTimer)
      clearTimeout(doneTimer)
    }
  }, [rows])

  if (isDone || rows == null) return null

  const centerR = (rows - 1) / 2
  const centerC = (COLS - 1) / 2
  const maxDist = Math.sqrt(centerC * centerC + centerR * centerR)

  return (
    <div
      className={`page-reveal ${isRevealed ? 'is-revealed' : ''}`}
      style={{ gridTemplateRows: `repeat(${rows}, 1fr)` }}
      aria-hidden="true"
    >
      {Array.from({ length: rows }).map((_, r) =>
        Array.from({ length: COLS }).map((_, c) => (
          <div
            key={`${r}-${c}`}
            className="page-reveal__tile"
            style={{ transitionDelay: `${getTileDelay(r, c, centerR, centerC, maxDist)}s` }}
          />
        ))
      )}
    </div>
  )
}