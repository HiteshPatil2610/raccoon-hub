import { useEffect, useLayoutEffect, useState } from 'react'
import './PageRevealOverlay.css'

const COLS = 25
const TILE_DURATION_SECONDS = 0.8
const LEVEL_FOUR_START_PROGRESS = 0.95
const REVEAL_START_DELAY_MS = 500

function getStartBounds(rows, cols) {
  const centerRows = rows % 2 === 0 ? 2 : 1
  const centerCols = cols % 2 === 0 ? 2 : 1
  const hasTwoByTwoCenter = centerRows === 2 && centerCols === 2

  // 1x1 -> 3x3, 1x2 -> 3x4, 2x1 -> 4x3. A true 2x2 starts as 2x2.
  const height = hasTwoByTwoCenter ? 2 : centerRows + 2
  const width = hasTwoByTwoCenter ? 2 : centerCols + 2
  const top = Math.floor((rows - height) / 2)
  const left = Math.floor((cols - width) / 2)

  return { top, bottom: top + height - 1, left, right: left + width - 1 }
}

function isInStartGroup(r, c, bounds) {
  return r >= bounds.top && r <= bounds.bottom && c >= bounds.left && c <= bounds.right
}

function getTileLevel(r, c, bounds, centerR, centerC) {
  if (isInStartGroup(r, c, bounds)) return 1

  // Once the special level-one group has started, all later rings are measured
  // from the grid's original mathematical center, not from that group's edges.
  const radius = Math.hypot(r - centerR, c - centerC)
  return Math.max(2, Math.floor(radius))
}

function getTileDelay(r, c, bounds, centerR, centerC) {
  // Levels 2 and 3 are evenly placed between 1 and 4. Therefore level 4
  // starts when level 1 is 95% complete (5% remains).
  const levelInterval = (TILE_DURATION_SECONDS * LEVEL_FOUR_START_PROGRESS) / 3
  return (getTileLevel(r, c, bounds, centerR, centerC) - 1) * levelInterval
}

function getTotalLifetimeMs(rows) {
  const bounds = getStartBounds(rows, COLS)
  const centerR = (rows - 1) / 2
  const centerC = (COLS - 1) / 2
  const finalDelay = getTileDelay(0, 0, bounds, centerR, centerC)
  return REVEAL_START_DELAY_MS + (finalDelay + TILE_DURATION_SECONDS) * 1000 + 100
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
    const doneTimer = setTimeout(() => setIsDone(true), getTotalLifetimeMs(rows))

    return () => {
      clearTimeout(revealTimer)
      clearTimeout(doneTimer)
    }
  }, [rows])

  if (isDone || rows == null) return null

  const startBounds = getStartBounds(rows, COLS)
  const centerR = (rows - 1) / 2
  const centerC = (COLS - 1) / 2

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
            style={{ transitionDelay: `${getTileDelay(r, c, startBounds, centerR, centerC)}s` }}
          />
        ))
      )}
    </div>
  )
}