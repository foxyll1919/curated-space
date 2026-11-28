import { useCallback, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { ThemeToggle } from '@/components/ThemeToggle'
import './landing.css'

function FlipCard({
  num,
  title,
  desc,
  back,
}: {
  num: string
  title: string
  desc: string
  back: React.ReactNode
}) {
  const ref = useRef<HTMLDivElement>(null)

  const flip = useCallback(() => {
    const el = ref.current
    if (!el) return
    el.classList.toggle('flipped')
    const backEl = el.querySelector('.ld-card-back')
    if (backEl) backEl.setAttribute('aria-hidden', el.classList.contains('flipped') ? 'false' : 'true')
  }, [])

  return (
    <div className="ld-card-wrap ld-reveal">
      <div
        ref={ref}
        className="ld-card-flip"
        role="button"
        tabIndex={0}
        aria-label={`${title} — press to see illustration`}
        onClick={flip}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); flip() } }}
      >
        <div className="ld-card-face ld-card-front">
          <div className="ld-card-hole" />
          <div className="ld-card-accent" />
          <div className="ld-card-body">
            <span className="ld-card-num">{num}</span>
            <h3 className="ld-card-title">{title}</h3>
            <p className="ld-card-desc">{desc}</p>
            <span className="ld-card-hint">click to flip ↻</span>
          </div>
        </div>
        <div className="ld-card-face ld-card-back" aria-hidden="true">
          {back}
        </div>
      </div>
    </div>
  )
}

function DropBack() {
  return (
    <>
      <div className="ld-back-dropzone">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="7 10 12 15 17 10" />
          <line x1="12" y1="15" x2="12" y2="3" />
        </svg>
      </div>
      <span className="ld-back-label">DRAG &amp; DROP</span>
    </>
  )
}

function ShimmerBack() {
  return (
    <>
      <div className="ld-back-shimmer" />
      <div className="ld-back-shimmer-lines">
        <div className="ld-back-shimmer-line" />
        <div className="ld-back-shimmer-line" />
        <div className="ld-back-shimmer-line" />
      </div>
      <span className="ld-back-label">EXTRACTING…</span>
    </>
  )
}

function SearchBack() {
  return (
    <>
      <div className="ld-back-search">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <div className="ld-back-cursor" />
      </div>
      <div className="ld-back-results">
        <div className="ld-back-result" />
        <div className="ld-back-result" />
        <div className="ld-back-result" />
      </div>
      <span className="ld-back-label">SEARCH</span>
    </>
  )
}

const LABELS = [
  {
    name: 'Your Personal Archive',
    desc: 'Every screenshot is securely stored in your account. Only you can see, search, and manage your collection.',
    medium: 'Medium: Encrypted sessions & per-account isolation',
  },
  {
    name: 'The Ask Room',
    desc: 'Ask your library questions in plain English. Answers cite the original screenshots so you can verify every claim.',
    medium: 'Medium: Retrieval-augmented generation',
  },
  {
    name: 'The Catalogue',
    desc: 'Every screenshot is titled, described, and tagged automatically. Corrections are yours to make at any time.',
    medium: 'Medium: Structured metadata extraction',
  },
  {
    name: 'Responsible AI',
    desc: 'Screenshots are sent to Gemini only for analysis — never for model training. You can skip analysis entirely for sensitive screenshots.',
    medium: 'Medium: Gemini API with data-use safeguards',
  },
]

export function LandingPage() {
  const fillRef = useRef<HTMLDivElement>(null)
  const guideRef = useRef<HTMLDivElement>(null)
  const guideDismissed = useRef(false)

  useEffect(() => {
    const els = document.querySelectorAll('.ld-reveal')
    if (!('IntersectionObserver' in window)) {
      els.forEach((el) => el.classList.add('visible'))
      return
    }
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible')
            io.unobserve(entry.target)
          }
        }
      },
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' },
    )
    els.forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [])

  useEffect(() => {
    function onScroll() {
      // Guide
      if (!guideDismissed.current && guideRef.current) {
        guideDismissed.current = true
        guideRef.current.classList.add('hidden')
      }

      // Timeline fill
      const y = window.scrollY
      const h = document.documentElement.scrollHeight - window.innerHeight
      const pct = h > 0 ? (y / h) * 100 : 0
      if (fillRef.current) fillRef.current.style.height = `${Math.min(pct, 100)}%`

      // Timeline dots
      const sections = document.querySelectorAll<HTMLElement>('[data-si]')
      sections.forEach((sec) => {
        const idx = sec.getAttribute('data-si')
        const rect = sec.getBoundingClientRect()
        const mid = rect.top + rect.height / 2
        const dot = document.querySelector(`.ld-timeline-dot[data-sec="${idx}"]`)
        if (dot) dot.classList.toggle('active', mid < window.innerHeight * 0.6)
      })
    }

    window.addEventListener('scroll', onScroll, { passive: true })
    onScroll()
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div className="landing">
      {/* Theme toggle */}
      <div style={{ position: 'fixed', top: '1.25rem', right: '1.25rem', zIndex: 100 }}>
        <ThemeToggle />
      </div>

      {/* Timeline */}
      <div className="ld-timeline" aria-hidden="true">
        <div className="ld-timeline-fill" ref={fillRef} />
        <div className="ld-timeline-dot" data-sec="0" style={{ top: '12%' }} />
        <div className="ld-timeline-dot" data-sec="1" style={{ top: '32%' }} />
        <div className="ld-timeline-dot" data-sec="2" style={{ top: '54%' }} />
        <div className="ld-timeline-dot" data-sec="3" style={{ top: '72%' }} />
        <div className="ld-timeline-dot" data-sec="4" style={{ top: '88%' }} />
      </div>

      {/* Guide */}
      <div className="ld-guide" ref={guideRef} role="status" aria-live="polite">
        <span className="ld-guide-dot" />
        Scroll to explore the exhibition
      </div>

      {/* ═══ HERO ═══ */}
      <header className="ld-hero" data-si="0">
        <span className="ld-hero-number ld-reveal">NO. 001 — PERSONAL KNOWLEDGE LIBRARY</span>
        <img src="/favicon.jpg" alt="Curated Space" className="ld-hero-logo ld-reveal" width={60} height={60} fetchPriority="high" />
        <h1 className="ld-hero-title ld-reveal">Curated Space</h1>
        <hr className="ld-hero-rule ld-reveal" />
        <p className="ld-hero-sub ld-reveal">A personal library for your visual references, powered by&nbsp;AI.</p>
        <Link to="/login" className="ld-btn ld-reveal">Enter the library →</Link>
      </header>

      {/* ═══ HOW IT WORKS ═══ */}
      <section className="ld-section" data-si="1" aria-labelledby="ld-how">
        <p className="ld-section-label ld-reveal" id="ld-how">HOW IT WORKS</p>
        <div className="ld-cards ld-stagger">
          <FlipCard num="NO. 001" title="Drop it in" desc="Screenshots arrive by drop, paste, or file pick. Each one is stored and catalogued." back={<DropBack />} />
          <FlipCard num="NO. 002" title="AI catalogues it" desc="Gemini reads your screenshot and writes a title, description, and tags." back={<ShimmerBack />} />
          <FlipCard num="NO. 003" title="Find it again" desc="Full-text search, semantic search, or just ask a question in plain English." back={<SearchBack />} />
        </div>
      </section>

      {/* ═══ FEATURES ═══ */}
      <section className="ld-section" data-si="2" aria-labelledby="ld-feat">
        <p className="ld-section-label ld-reveal" id="ld-feat">THE COLLECTION</p>
        <div className="ld-labels ld-stagger">
          {LABELS.map((l) => (
            <article key={l.name} className="ld-label ld-reveal">
              <h3 className="ld-label-name">{l.name}</h3>
              <p className="ld-label-desc">{l.desc}</p>
              <span className="ld-label-medium">{l.medium}</span>
            </article>
          ))}
        </div>
      </section>

      {/* ═══ CTA ═══ */}
      <section className="ld-cta" data-si="3" aria-label="Get started">
        <div className="ld-cta-ornament ld-reveal">
          <div className="ld-cta-line" />
          <div className="ld-cta-diamond" />
          <div className="ld-cta-line" />
        </div>
        <h2 className="ld-cta-heading ld-reveal">Sign the visitor book to begin your collection.</h2>
        <p className="ld-cta-sub ld-reveal">Every screenshot you save becomes a permanent entry in your personal archive.</p>
        <Link to="/login" className="ld-btn ld-reveal">Create your account →</Link>
        <p className="ld-cta-fine ld-reveal">Free to use · No credit card required</p>
      </section>

      {/* ═══ AI ETHICS ═══ */}
      <section className="ld-ethics" data-si="4" aria-labelledby="ld-ethics-h">
        <h3 className="ld-ethics-heading ld-reveal" id="ld-ethics-h">A note on AI and your screenshots</h3>
        <p className="ld-ethics-body ld-reveal">
          Curated Space uses Google Gemini to read your screenshots and extract titles, descriptions and tags.
          Screenshots are sent to the Gemini API for analysis only&nbsp;— they are not used to train models.
          You can save any screenshot without analysis by toggling "Don't analyze," and it will never be sent to any AI&nbsp;provider.
          Review Google's{' '}
          <a href="https://ai.google.dev/gemini-api/terms" target="_blank" rel="noopener noreferrer">Gemini&nbsp;API&nbsp;terms</a>
          {' '}and{' '}
          <a href="https://ai.google.dev/gemini-api/docs/billing" target="_blank" rel="noopener noreferrer">billing&nbsp;tiers</a>
          {' '}for complete data-handling details.
        </p>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer className="ld-footer">
        <div className="ld-footer-inner">
          <div className="ld-footer-row">
            <img src="/favicon.jpg" alt="" className="ld-footer-logo" width={18} height={18} loading="lazy" />
            <span className="ld-footer-text">© 2026 Curated Space</span>
          </div>
          <div className="ld-footer-row">
            <a href="https://github.com/foxyll1919/curated-space" className="ld-footer-link" target="_blank" rel="noopener noreferrer">GitHub</a>
            <span className="ld-footer-sep" aria-hidden="true">·</span>
            <Link to="/login" className="ld-footer-link">Sign in</Link>
            <span className="ld-footer-sep" aria-hidden="true">·</span>
            <a href="https://ai.google.dev/gemini-api/terms" className="ld-footer-link" target="_blank" rel="noopener noreferrer">AI terms</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
