import { useEffect, useState } from 'react'
import './HeroPixelReveal.css'

const ROWS = 13
const COLS = 25
const CENTER_R = (ROWS - 1) / 2 // 6
const CENTER_C = (COLS - 1) / 2 // 12
const SPREAD_SECONDS = 1.2

/**
 * One-time square-ripple pixel reveal, purely decorative. Plays once
 * automatically shortly after mount and then stays revealed - no
 * controls, no re-trigger, no pattern/theme/speed pickers. Those exist
 * in the original reference component this was adapted from, but were
 * deliberately stripped for the live site to avoid UI clutter.
 */
function getTileDelay(r, c, revealing) {
  const dist = Math.max(Math.abs(r - CENTER_R), Math.abs(c - CENTER_C))
  const maxDist = Math.max(CENTER_R, CENTER_C)
  const norm = dist / maxDist
  return (revealing ? norm : 1 - norm) * SPREAD_SECONDS
}

export default function HeroPixelReveal() {
  const [isRevealed, setIsRevealed] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setIsRevealed(true), 400)
    return () => clearTimeout(timer)
  }, [])

  return (
    <section className="hero-pixel">
      <div className="hero-pixel__backdrop">
        <div className="hero-pixel__glow hero-pixel__glow--a" />
        <div className="hero-pixel__glow hero-pixel__glow--b" />
        <div className="hero-pixel__glow hero-pixel__glow--c" />
        <div className="hero-pixel__dots" />

        <div className="hero-pixel__content">
          <h1 className="hero-pixel__title">Raccoon Hub</h1>
          <p className="hero-pixel__subtitle">Hand-picked gear, straight to Amazon.</p>
        </div>
      </div>

      <div className="hero-pixel__grid">
        {Array.from({ length: ROWS }).map((_, r) =>
          Array.from({ length: COLS }).map((_, c) => {
            const delay = getTileDelay(r, c, isRevealed)
            return (
              <div
                key={`${r}-${c}`}
                className="hero-pixel__tile"
                style={{
                  transform: isRevealed ? 'scale(0)' : 'scale(1)',
                  opacity: isRevealed ? 0 : 1,
                  transitionDelay: `${delay}s`,
                }}
              />
            )
          })
        )}
      </div>
    </section>
  )
}