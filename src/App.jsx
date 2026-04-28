import { useState, useCallback, useRef, useEffect } from 'react'
import { processPhoto, runTryOn, warmUp } from './api.js'
import { loadGarments } from './garments.js'

const PREFETCH_AHEAD = 2

// ─── UPLOAD SCREEN ──────────────────────────────────────────────────────────
function UploadScreen({ onPhotoReady }) {
  const [dragging, setDragging]     = useState(false)
  const [preview, setPreview]       = useState(null)
  const [file, setFile]             = useState(null)
  const [processing, setProcessing] = useState(false)
  const [error, setError]           = useState(null)
  const inputRef = useRef()

  const handleFile = useCallback((f) => {
    if (!f || !f.type.startsWith('image/')) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setError(null)
  }, [])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }, [handleFile])

  const onStart = async () => {
    if (!file) return
    setProcessing(true)
    setError(null)
    try {
      const { session_id } = await processPhoto(file)
      warmUp()
      onPhotoReady({ sessionId: session_id, photoUrl: preview })
    } catch (err) {
      setError(err.message)
      setProcessing(false)
    }
  }

  return (
    <div style={s.uploadScreen}>
      <div style={s.grain} />

      <header style={s.uploadHeader}>
        <span style={s.logo}>DRAPE</span>
        <span style={s.logoSub}>Virtual Try-On</span>
      </header>

      <div style={s.hero}>
        <h1 style={s.heroTitle}>
          See it on<br />
          <em>you.</em>
        </h1>
        <p style={s.heroSub}>
          Upload a photo. Browse the collection.<br />
          Watch the clothes fit to your body — instantly.
        </p>
      </div>

      <div
        style={{
          ...s.dropzone,
          ...(dragging ? s.dropzoneDrag : {}),
          ...(preview ? s.dropzoneHasPhoto : {}),
        }}
        onClick={() => inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
        {preview ? (
          <div style={s.previewWrapper}>
            <img src={preview} alt="Your photo" style={s.previewImg} />
            <div style={s.previewOverlay}>
              <span style={s.previewChange}>Change photo</span>
            </div>
          </div>
        ) : (
          <div style={s.dropzoneInner}>
            <div style={s.uploadIcon}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
              </svg>
            </div>
            <p style={s.dropzoneText}>Drop your photo here</p>
            <p style={s.dropzoneSub}>or click to browse · JPG, PNG, WEBP</p>
            <p style={s.dropzoneTip}>
              Best results: stand straight, arms slightly away from body, good lighting
            </p>
          </div>
        )}
      </div>

      {error && <p style={s.errorMsg}>{error}</p>}

      <button
        style={{ ...s.ctaBtn, ...((!file || processing) ? s.ctaBtnDisabled : {}) }}
        onClick={onStart}
        disabled={!file || processing}
      >
        {processing ? (
          <span style={s.ctaBtnInner}><span style={s.spinner} />Preparing your session…</span>
        ) : (
          <span style={s.ctaBtnInner}>
            Start Styling
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </span>
        )}
      </button>
    </div>
  )
}

// ─── GARMENT CARD ────────────────────────────────────────────────────────────
function GarmentCard({ garment, isSelected, isLoading, isCached, onClick }) {
  return (
    <button
      style={{ ...s.card, ...(isSelected ? s.cardSelected : {}) }}
      onClick={onClick}
      title={garment.label}
    >
      <div style={s.cardImgWrap}>
        <img
          src={garment.image}
          alt={garment.label}
          style={s.cardImg}
          onError={(e) => { e.target.style.opacity = 0.3 }}
        />
        {isSelected && isLoading && (
          <div style={s.cardLoadOverlay}><span style={s.spinnerSm} /></div>
        )}
        {isCached && !isSelected && (
          <div style={s.cachedDot} title="Ready" />
        )}
      </div>
      <div style={s.cardMeta}>
        <span style={s.cardLabel}>{garment.label}</span>
        {garment.sub && <span style={s.cardSub}>{garment.sub}</span>}
        {garment.tags?.length > 0 && (
          <div style={s.cardTags}>
            {garment.tags.map(t => (
              <span key={t} style={s.tag}>{t}</span>
            ))}
          </div>
        )}
      </div>
    </button>
  )
}

// ─── SKELETON CARD (shown while Claude analyzes) ─────────────────────────────
function SkeletonCard() {
  return (
    <div style={s.skeleton}>
      <div style={s.skeletonImg} />
      <div style={s.skeletonMeta}>
        <div style={{ ...s.skeletonLine, width: '70%' }} />
        <div style={{ ...s.skeletonLine, width: '50%' }} />
      </div>
    </div>
  )
}

// ─── TRY-ON SCREEN ───────────────────────────────────────────────────────────
function TryOnScreen({ sessionId, photoUrl, onReset }) {
  const [tab, setTab]               = useState('upper')
  const [selectedUpper, setSelectedUpper] = useState(null)
  const [selectedLower, setSelectedLower] = useState(null)
  const [resultUpper, setResultUpper]     = useState(null)
  const [resultLower, setResultLower]     = useState(null)
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState(null)
  const [library, setLibrary]       = useState({ upper: [], lower: [] })
  const [analyzing, setAnalyzing]   = useState(true)   // Claude is reading garments
  const cache          = useRef({})
  const prefetchQueue  = useRef(new Set())

  // Load + analyze all garments on mount
  useEffect(() => {
    loadGarments()
      .then(lib => {
        setLibrary(lib)
        setAnalyzing(false)
      })
      .catch(err => {
        console.error('loadGarments failed:', err)
        setAnalyzing(false)
      })
  }, [])

  const garments   = tab === 'upper' ? library.upper : library.lower
  const selectedId = tab === 'upper' ? selectedUpper?.id : selectedLower?.id

  const displayImage = (() => {
    if (resultUpper && !resultLower) return resultUpper
    if (resultLower && !resultUpper) return resultLower
    if (resultUpper && resultLower)  return resultUpper
    return photoUrl
  })()

  const fetchTryOn = useCallback(async (garment, background = false) => {
    const key = garment.id
    if (cache.current[key]) return cache.current[key]
    if (prefetchQueue.current.has(key)) return null

    prefetchQueue.current.add(key)
    try {
      const garmentUrl = window.location.origin + garment.image
      const url = await runTryOn(sessionId, garmentUrl, garment.type)
      cache.current[key] = url
      return url
    } catch (err) {
      if (!background) throw err
      return null
    } finally {
      prefetchQueue.current.delete(key)
    }
  }, [sessionId])

  const prefetchNext = useCallback((currentIndex) => {
    const list = tab === 'upper' ? library.upper : library.lower
    for (let i = 1; i <= PREFETCH_AHEAD; i++) {
      const next = list[currentIndex + i]
      if (next && !cache.current[next.id]) fetchTryOn(next, true)
    }
  }, [tab, library, fetchTryOn])

  const selectGarment = useCallback(async (garment, index) => {
    setError(null)

    if (cache.current[garment.id]) {
      const url = cache.current[garment.id]
      if (garment.type === 'upper') { setSelectedUpper(garment); setResultUpper(url) }
      else                          { setSelectedLower(garment); setResultLower(url) }
      prefetchNext(index)
      return
    }

    if (garment.type === 'upper') setSelectedUpper(garment)
    else                          setSelectedLower(garment)
    setLoading(true)

    try {
      const url = await fetchTryOn(garment)
      if (garment.type === 'upper') setResultUpper(url)
      else                          setResultLower(url)
      prefetchNext(index)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [fetchTryOn, prefetchNext])

  const handleSave = () => {
    const a = document.createElement('a')
    a.href = displayImage
    a.download = 'drape-look.png'
    a.click()
  }

  return (
    <div style={s.tryonScreen}>
      {/* ── Left: Result canvas ── */}
      <div style={s.canvas}>
        <div style={s.canvasInner}>
          <img
            key={displayImage}
            src={displayImage}
            alt="Try-on result"
            style={{ ...s.resultImg, animation: 'fadeIn 0.4s ease' }}
          />
          {loading && (
            <div style={s.canvasOverlay}>
              <div style={s.generatingBadge}>
                <span style={s.spinner} />
                <span>Generating…</span>
              </div>
            </div>
          )}
        </div>

        <div style={s.canvasActions}>
          <button style={s.resetBtn} onClick={onReset}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 12a9 9 0 109-9M3 3v5h5" />
            </svg>
            New photo
          </button>
          <button
            style={{ ...s.saveBtn, ...(displayImage === photoUrl ? s.saveBtnDisabled : {}) }}
            onClick={handleSave}
            disabled={displayImage === photoUrl}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" />
            </svg>
            Save Look
          </button>
        </div>
      </div>

      {/* ── Right: Garment panel ── */}
      <div style={s.panel}>
        <div style={s.panelHeader}>
          <span style={s.logoPanelLarge}>DRAPE</span>
          {analyzing && (
            <div style={s.analyzingBadge}>
              <span style={s.spinnerXs} />
              <span>Cataloguing collection…</span>
            </div>
          )}
          {error && <p style={s.errorInline}>{error}</p>}
        </div>

        <div style={s.tabRow}>
          {['upper', 'lower'].map(t => (
            <button
              key={t}
              style={{ ...s.tab, ...(tab === t ? s.tabActive : {}) }}
              onClick={() => setTab(t)}
            >
              {t === 'upper' ? 'Upper Body' : 'Lower Body'}
            </button>
          ))}
        </div>

        <div style={s.statusRow}>
          {tab === 'upper'
            ? (selectedUpper
                ? <span style={s.statusSelected}>{selectedUpper.label}</span>
                : <span style={s.statusNone}>Select an item to try on</span>)
            : (selectedLower
                ? <span style={s.statusSelected}>{selectedLower.label}</span>
                : <span style={s.statusNone}>Select an item to try on</span>)
          }
        </div>

        <div style={s.garmentGrid}>
          {analyzing
            // Show skeletons while Claude analyzes
            ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
            : garments.map((g, i) => (
                <GarmentCard
                  key={g.id}
                  garment={g}
                  isSelected={g.id === selectedId}
                  isLoading={loading && g.id === selectedId}
                  isCached={!!cache.current[g.id]}
                  onClick={() => selectGarment(g, i)}
                />
              ))
          }
        </div>

        {(selectedUpper || selectedLower) && (
          <div style={s.outfitSummary}>
            <span style={s.summaryLabel}>Current outfit</span>
            <div style={s.summaryItems}>
              {selectedUpper && <span style={s.summaryItem}>↑ {selectedUpper.label}</span>}
              {selectedLower && <span style={s.summaryItem}>↓ {selectedLower.label}</span>}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── ROOT APP ────────────────────────────────────────────────────────────────
export default function App() {
  const [session, setSession] = useState(null)

  if (!session) return <UploadScreen onPhotoReady={setSession} />

  return (
    <TryOnScreen
      sessionId={session.sessionId}
      photoUrl={session.photoUrl}
      onReset={() => setSession(null)}
    />
  )
}

// ─── STYLES ──────────────────────────────────────────────────────────────────
const s = {
  uploadScreen: {
    height: '100vh', width: '100vw',
    display: 'flex', flexDirection: 'column',
    alignItems: 'center', justifyContent: 'center',
    gap: 28, padding: '40px 24px',
    position: 'relative', overflow: 'hidden',
    background: 'radial-gradient(ellipse at 30% 20%, #1a1408 0%, #0c0c0c 60%)',
    animation: 'fadeIn 0.6s ease',
  },
  grain: {
    position: 'absolute', inset: 0,
    backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E")`,
    pointerEvents: 'none', opacity: 0.6,
  },
  uploadHeader: {
    position: 'absolute', top: 32, left: 40,
    display: 'flex', alignItems: 'baseline', gap: 10,
  },
  logo: {
    fontFamily: 'var(--font-display)', fontSize: 22,
    fontWeight: 600, letterSpacing: '0.18em', color: 'var(--gold)',
  },
  logoSub: {
    fontFamily: 'var(--font-body)', fontSize: 11,
    fontWeight: 400, letterSpacing: '0.12em',
    color: 'var(--muted)', textTransform: 'uppercase',
  },
  hero: { textAlign: 'center', animation: 'fadeUp 0.7s ease both' },
  heroTitle: {
    fontFamily: 'var(--font-display)',
    fontSize: 'clamp(48px, 8vw, 80px)',
    fontWeight: 300, lineHeight: 1.05,
    color: 'var(--cream)', letterSpacing: '-0.01em',
  },
  heroSub: {
    marginTop: 16, fontSize: 15, fontWeight: 300,
    lineHeight: 1.7, color: 'var(--muted)', letterSpacing: '0.02em',
  },
  dropzone: {
    width: '100%', maxWidth: 480,
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-lg)',
    background: 'var(--surface)',
    cursor: 'pointer', transition: 'var(--transition)',
    animation: 'fadeUp 0.8s 0.1s ease both',
    overflow: 'hidden', minHeight: 180,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  dropzoneDrag: { border: '1px solid var(--gold-dim)', background: '#1a1508' },
  dropzoneHasPhoto: { border: '1px solid var(--gold-dim)', minHeight: 260 },
  dropzoneInner: {
    display: 'flex', flexDirection: 'column',
    alignItems: 'center', gap: 8, padding: '40px 24px', textAlign: 'center',
  },
  uploadIcon: { color: 'var(--gold-dim)', marginBottom: 8 },
  dropzoneText: { fontSize: 15, fontWeight: 400, color: 'var(--cream)' },
  dropzoneSub: { fontSize: 12, color: 'var(--muted)' },
  dropzoneTip: {
    marginTop: 12, fontSize: 11, color: '#3a3a3a',
    maxWidth: 300, lineHeight: 1.5,
  },
  previewWrapper: { width: '100%', position: 'relative', maxHeight: 320, overflow: 'hidden' },
  previewImg: { width: '100%', height: 320, objectFit: 'cover', display: 'block' },
  previewOverlay: {
    position: 'absolute', inset: 0,
    background: 'rgba(0,0,0,0.5)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  previewChange: { fontSize: 13, color: 'var(--cream)', letterSpacing: '0.08em' },
  errorMsg: { fontSize: 13, color: 'var(--danger)', maxWidth: 480, textAlign: 'center' },
  ctaBtn: {
    padding: '14px 36px', background: 'var(--gold)', color: '#0c0c0c',
    borderRadius: 'var(--radius-sm)', fontSize: 14, fontWeight: 500,
    letterSpacing: '0.06em', textTransform: 'uppercase',
    transition: 'var(--transition)', animation: 'fadeUp 0.8s 0.2s ease both', cursor: 'pointer',
  },
  ctaBtnDisabled: { opacity: 0.35, cursor: 'not-allowed' },
  ctaBtnInner: { display: 'flex', alignItems: 'center', gap: 10 },

  // Try-on screen
  tryonScreen: { height: '100vh', width: '100vw', display: 'flex', overflow: 'hidden', animation: 'fadeIn 0.5s ease' },

  // Canvas (left)
  canvas: { flex: '1 1 60%', display: 'flex', flexDirection: 'column', background: '#0e0e0e', position: 'relative', overflow: 'hidden' },
  canvasInner: { flex: 1, position: 'relative', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  resultImg: { height: '100%', width: '100%', objectFit: 'contain', display: 'block' },
  canvasOverlay: {
    position: 'absolute', inset: 0,
    background: 'rgba(12,12,12,0.6)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    backdropFilter: 'blur(4px)',
  },
  generatingBadge: {
    display: 'flex', alignItems: 'center', gap: 12,
    padding: '12px 24px', background: 'var(--surface)',
    border: '1px solid var(--border)', borderRadius: 100,
    fontSize: 13, letterSpacing: '0.04em', color: 'var(--cream)',
  },
  canvasActions: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '16px 24px', borderTop: '1px solid var(--border)', background: 'var(--bg)',
  },
  resetBtn: {
    display: 'flex', alignItems: 'center', gap: 8,
    fontSize: 13, color: 'var(--muted)', padding: '8px 14px',
    borderRadius: 'var(--radius-sm)', transition: 'var(--transition)',
    border: '1px solid transparent',
  },
  saveBtn: {
    display: 'flex', alignItems: 'center', gap: 8,
    fontSize: 13, fontWeight: 500, color: '#0c0c0c',
    background: 'var(--gold)', padding: '10px 20px',
    borderRadius: 'var(--radius-sm)', letterSpacing: '0.04em', transition: 'var(--transition)',
  },
  saveBtnDisabled: { opacity: 0.3, cursor: 'not-allowed' },

  // Panel (right)
  panel: {
    flex: '0 0 360px', display: 'flex', flexDirection: 'column',
    background: 'var(--surface)', borderLeft: '1px solid var(--border)', overflow: 'hidden',
  },
  panelHeader: { padding: '24px 24px 0', display: 'flex', flexDirection: 'column', gap: 8 },
  logoPanelLarge: { fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 600, letterSpacing: '0.2em', color: 'var(--gold)' },
  analyzingBadge: {
    display: 'flex', alignItems: 'center', gap: 8,
    fontSize: 11, color: 'var(--muted)', letterSpacing: '0.04em',
  },
  errorInline: { fontSize: 12, color: 'var(--danger)' },

  tabRow: {
    display: 'flex', margin: '16px 24px 0',
    background: 'var(--surface2)', borderRadius: 'var(--radius-sm)',
    padding: 3, gap: 2,
  },
  tab: {
    flex: 1, padding: '8px 0', fontSize: 12, fontWeight: 400,
    letterSpacing: '0.06em', textTransform: 'uppercase',
    color: 'var(--muted)', borderRadius: 4, transition: 'var(--transition)',
  },
  tabActive: { background: 'var(--border)', color: 'var(--cream)' },

  statusRow: {
    padding: '12px 24px', borderBottom: '1px solid var(--border)',
    minHeight: 40, display: 'flex', alignItems: 'center',
  },
  statusSelected: { fontSize: 13, color: 'var(--gold)', fontWeight: 400 },
  statusNone: { fontSize: 12, color: 'var(--muted)', fontStyle: 'italic' },

  garmentGrid: {
    flex: 1, overflowY: 'auto', padding: '16px',
    display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, alignContent: 'start',
  },

  // Garment card
  card: {
    background: 'var(--surface2)', border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)', overflow: 'hidden', cursor: 'pointer',
    transition: 'var(--transition)', textAlign: 'left',
    display: 'flex', flexDirection: 'column',
  },
  cardSelected: { border: '1px solid var(--gold-dim)', background: '#1a1508' },
  cardImgWrap: { position: 'relative', aspectRatio: '4/5', background: '#1a1a1a', overflow: 'hidden' },
  cardImg: { width: '100%', height: '100%', objectFit: 'cover', display: 'block', transition: 'transform 0.4s ease' },
  cardLoadOverlay: { position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  cachedDot: { position: 'absolute', top: 8, right: 8, width: 7, height: 7, borderRadius: '50%', background: 'var(--gold)' },
  cardMeta: { padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 3 },
  cardLabel: { fontSize: 12, fontWeight: 500, color: 'var(--cream)', letterSpacing: '0.02em' },
  cardSub: { fontSize: 10, color: 'var(--muted)', letterSpacing: '0.03em' },
  cardTags: { display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 },
  tag: {
    fontSize: 9, padding: '2px 6px', borderRadius: 3,
    background: 'var(--border)', color: 'var(--muted)',
    letterSpacing: '0.04em', textTransform: 'uppercase',
  },

  // Skeleton card
  skeleton: {
    background: 'var(--surface2)', border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)', overflow: 'hidden',
    display: 'flex', flexDirection: 'column',
  },
  skeletonImg: {
    aspectRatio: '4/5',
    background: 'linear-gradient(90deg, var(--surface2) 25%, var(--border) 50%, var(--surface2) 75%)',
    backgroundSize: '200% 100%',
    animation: 'shimmer 1.5s infinite',
  },
  skeletonMeta: { padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 6 },
  skeletonLine: {
    height: 8, borderRadius: 4,
    background: 'linear-gradient(90deg, var(--surface2) 25%, var(--border) 50%, var(--surface2) 75%)',
    backgroundSize: '200% 100%',
    animation: 'shimmer 1.5s infinite',
  },

  // Outfit summary
  outfitSummary: { padding: '14px 24px', borderTop: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 6 },
  summaryLabel: { fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)' },
  summaryItems: { display: 'flex', flexDirection: 'column', gap: 2 },
  summaryItem: { fontSize: 13, color: 'var(--cream)' },

  // Spinners
  spinner: {
    display: 'inline-block', width: 16, height: 16,
    border: '2px solid rgba(0,0,0,0.2)', borderTopColor: '#0c0c0c',
    borderRadius: '50%', animation: 'spin 0.7s linear infinite', flexShrink: 0,
  },
  spinnerSm: {
    display: 'inline-block', width: 20, height: 20,
    border: '2px solid rgba(255,255,255,0.2)', borderTopColor: '#fff',
    borderRadius: '50%', animation: 'spin 0.7s linear infinite',
  },
  spinnerXs: {
    display: 'inline-block', width: 10, height: 10,
    border: '1.5px solid rgba(255,255,255,0.15)', borderTopColor: 'var(--muted)',
    borderRadius: '50%', animation: 'spin 0.7s linear infinite',
  },
}
