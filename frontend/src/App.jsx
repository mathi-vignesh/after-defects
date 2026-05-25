import { useState, useRef, useCallback } from 'react'
import './App.css'

const API = '/api'

/* ─── Spinner ─── */
function Loader({ text }) {
  return (
    <div className="loading-state">
      <div className="loader"><div className="loader-ring" /></div>
      <div className="loader-text">{text}</div>
    </div>
  )
}

/* ─── Drop Zone ─── */
function DropZone({ onFile }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef(null)

  const handle = (f) => {
    if (!f) return
    const ext = f.name.split('.').pop().toLowerCase()
    if (!['aep', 'ffx'].includes(ext)) {
      alert('Only .aep and .ffx files are supported.')
      return
    }
    onFile(f)
  }

  const onDrop = useCallback((e) => {
    e.preventDefault(); setDragging(false); handle(e.dataTransfer.files[0])
  }, [])

  return (
    <div
      className={`dropzone ${dragging ? 'dragging' : ''}`}
      onClick={() => inputRef.current?.click()}
      onDrop={onDrop}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
    >
      <input ref={inputRef} type="file" accept=".aep,.ffx" style={{ display: 'none' }}
        onChange={(e) => handle(e.target.files[0])} />

      <div className="dz-icon">
        <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
          <path d="M18 24V12M18 12L13 17M18 12L23 17" stroke="currentColor" strokeWidth="1.5"
            strokeLinecap="round" strokeLinejoin="round"/>
          <rect x="4" y="4" width="28" height="28" rx="5" stroke="currentColor"
            strokeWidth="1" strokeDasharray="3 3" opacity="0.5"/>
        </svg>
      </div>

      <div className="dz-title">Drop your project file</div>
      <div className="dz-sub">or click anywhere to browse</div>

      <div className="dz-formats">
        <span className="dz-tag">.aep</span>
        <span className="dz-sep">·</span>
        <span className="dz-tag">.ffx</span>
        <span className="dz-sep">·</span>
        <span style={{ fontSize: 11, color: 'var(--dim)', fontFamily: 'var(--mono)' }}>max 512 mb</span>
      </div>
    </div>
  )
}

/* ─── File Loaded ─── */
function FileLoaded({ file, onRemove }) {
  const kb = (file.size / 1024)
  const size = kb > 1024 ? `${(kb/1024).toFixed(1)} MB` : `${kb.toFixed(0)} KB`
  return (
    <div className="file-loaded">
      <div className="file-icon">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M3 2h7l3 3v9H3V2z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round"/>
          <path d="M10 2v3h3" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round"/>
          <path d="M5 9h6M5 11h4" stroke="currentColor" strokeWidth="1" strokeLinecap="round" opacity="0.5"/>
        </svg>
      </div>
      <div className="file-info">
        <div className="file-name">{file.name}</div>
        <div className="file-size">{size}</div>
      </div>
      <button className="file-remove" onClick={onRemove} title="Remove">✕</button>
    </div>
  )
}

/* ─── Version Display ─── */
function VersionDisplay({ source }) {
  return (
    <div className="version-detected">
      <div className="vd-label">Detected source</div>
      <div className="vd-name">{source.version_name}</div>
      <div className="vd-appver">v{source.app_ver}</div>
    </div>
  )
}

/* ─── Target Grid ─── */
function TargetGrid({ targets, selected, onSelect, disabled }) {
  return (
    <div className="target-grid">
      {targets.map((t, i) => (
        <button
          key={t.byte}
          className={`ver-btn ${selected === t.byte ? 'selected' : ''}`}
          onClick={() => onSelect(t.byte)}
          disabled={disabled}
          style={{ animationDelay: `${i * 30}ms` }}
        >
          <span className="vb-short">{t.short}</span>
          <span className="vb-appver">{t.app_ver}</span>
        </button>
      ))}
    </div>
  )
}

/* ─── Warnings ─── */
function Warnings({ warnings }) {
  if (!warnings?.length) return null
  return (
    <div className="warnings">
      <div className="warn-title">
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M5 1L9 9H1L5 1Z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
        </svg>
        Heads up
      </div>
      <ul>{warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
    </div>
  )
}

/* ─── Main App ─── */
export default function App() {
  const [file,     setFile]     = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [selected, setSelected] = useState(null)
  const [phase,    setPhase]    = useState('idle')
  const [error,    setError]    = useState(null)
  const [result,   setResult]   = useState(null)

  const reset = () => {
    setFile(null); setAnalysis(null); setSelected(null)
    setPhase('idle'); setError(null); setResult(null)
  }

  const handleFile = async (f) => {
    setFile(f); setPhase('analyzing'); setError(null); setAnalysis(null); setSelected(null)
    try {
      const form = new FormData(); form.append('file', f)
      const res = await fetch(`${API}/analyze`, { method: 'POST', body: form })
      if (!res.ok) { const e = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(e.detail || 'Analysis failed') }
      setAnalysis(await res.json()); setPhase('ready')
    } catch (e) { setError(e.message); setPhase('error') }
  }

  const handleDowngrade = async () => {
    if (!selected || !file) return
    setPhase('converting'); setError(null)
    try {
      const form = new FormData(); form.append('file', file); form.append('target_version_int', selected)
      const res = await fetch(`${API}/downgrade`, { method: 'POST', body: form })
      if (!res.ok) { const e = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(e.detail || 'Downgrade failed') }
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const disp = res.headers.get('Content-Disposition') || ''
      const m    = disp.match(/filename="([^"]+)"/)
      const filename  = m ? m[1] : `downgraded.${file.name.split('.').pop()}`
      const rawWarn   = res.headers.get('X-Warnings') || ''
      const warnings  = rawWarn ? rawWarn.split(' | ').filter(Boolean) : []
      setResult({ url, filename, warnings }); setPhase('done')
    } catch (e) { setError(e.message); setPhase('ready') }
  }

  const triggerDownload = () => {
    if (!result) return
    const a = document.createElement('a'); a.href = result.url; a.download = result.filename; a.click()
  }

  const targetInfo = analysis?.targets?.find(t => t.byte === selected)
  const isConverting = phase === 'converting'

  return (
    <div className="app">

      {/* ── Header ── */}
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-ae">AE</span>
            <span className="logo-name"><span>Down</span>grader</span>
          </div>
          <div className="header-right">Binary · RIFX Patcher</div>
        </div>
      </header>

      {/* ── Hero ── */}
      <div className="hero">
        <div className="hero-eyebrow">Version Compatibility Tool</div>
        <h1 className="hero-title">
          Open older<br/><em>After Effects</em><br/>projects.
        </h1>
        <p className="hero-sub">
          Patch any .aep or .ffx file to open in older versions of After Effects.
          Binary-precise. No quality loss.
        </p>
      </div>

      {/* ── Main ── */}
      <main className="main">

        {/* Error */}
        {error && (
          <div className="error-panel">
            <div className="err-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.3"/>
                <path d="M8 5v3.5M8 10.5v.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
              </svg>
            </div>
            <div>
              <div className="err-title">Error</div>
              <div className="err-msg">{error}</div>
            </div>
            <button className="err-dismiss" onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {/* Step 1 — Upload */}
        <div className="panel" style={{ '--delay': '100ms' }}>
          <div className="panel-header">
            <span className="panel-num">01</span>
            <span className="panel-title">Upload File</span>
            <span className={`panel-status ${phase !== 'idle' ? 'done' : ''}`} />
          </div>
          <div className="panel-body">
            {phase === 'idle' ? (
              <DropZone onFile={handleFile} />
            ) : (
              <FileLoaded file={file} onRemove={reset} />
            )}
          </div>
        </div>

        {/* Step 2 — Detected Version */}
        {(phase === 'analyzing' || analysis) && (
          <div className="panel" style={{ '--delay': '0ms' }}>
            <div className="panel-header">
              <span className="panel-num">02</span>
              <span className="panel-title">Source Version</span>
              <span className={`panel-status ${analysis ? 'done' : 'active'}`} />
            </div>
            <div className="panel-body">
              {phase === 'analyzing'
                ? <Loader text={<><strong>Parsing</strong> RIFX structure…</>} />
                : <VersionDisplay source={analysis.source} />
              }
            </div>
          </div>
        )}

        {/* Step 3 — Target */}
        {analysis && (
          <div className="panel" style={{ '--delay': '0ms' }}>
            <div className="panel-header">
              <span className="panel-num">03</span>
              <span className="panel-title">Target Version</span>
              <span className={`panel-status ${selected ? 'done' : ''}`} />
            </div>
            <div className="panel-body">
              {analysis.targets.length === 0 ? (
                <p style={{ fontSize: 13, color: 'var(--mid)' }}>
                  No older versions available — this is the oldest supported version.
                </p>
              ) : (
                <TargetGrid
                  targets={analysis.targets}
                  selected={selected}
                  onSelect={(b) => { setSelected(b); setResult(null); if (phase === 'done') setPhase('ready') }}
                  disabled={isConverting}
                />
              )}
            </div>
          </div>
        )}

        {/* Step 4 — Convert */}
        {selected && (
          <div className="panel" style={{ '--delay': '0ms' }}>
            <div className="panel-header">
              <span className="panel-num">04</span>
              <span className="panel-title">Convert</span>
              <span className={`panel-status ${phase === 'done' ? 'done' : isConverting ? 'active' : ''}`} />
            </div>
            <div className="panel-body">

              {/* Conversion summary arrow */}
              <div className="conversion-row">
                <div className="conv-from">
                  <div className="conv-label">From</div>
                  <div className="conv-version">{analysis.source.version_short}</div>
                </div>
                <div className="conv-arrow">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M4 10h12M12 6l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <div className="conv-to">
                  <div className="conv-label">To</div>
                  <div className="conv-version">{targetInfo?.short}</div>
                </div>
              </div>

              {/* States */}
              {isConverting ? (
                <Loader text={<><strong>Patching</strong> version bytes…</>} />
              ) : phase === 'done' && result ? (
                <>
                  <div className="success-panel">
                    <div className="success-top">
                      <div className="success-icon">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                          <path d="M3 8l4 4 6-6" stroke="var(--ink)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <div className="success-label">File converted successfully</div>
                    </div>
                    <div className="success-filename">{result.filename}</div>
                    <Warnings warnings={result.warnings} />
                    <div className="btn-row">
                      <button className="btn-download-final" onClick={triggerDownload}>
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                          <path d="M7 1v8M7 9l-3-3M7 9l3-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M2 12h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                        </svg>
                        Download
                      </button>
                      <button className="btn-ghost" onClick={reset}>Convert another</button>
                    </div>
                  </div>
                </>
              ) : (
                <button className="btn-convert" onClick={handleDowngrade}>
                  Convert to {targetInfo?.short}
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path d="M7 1v8M7 9l-3-3M7 9l3-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M2 12h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                </button>
              )}
            </div>
          </div>
        )}

      </main>

      {/* ── Footer ── */}
      <footer className="footer">
        <div className="footer-left">
          <span>AE Downgrader</span>
          <span className="footer-dot">·</span>
          <span>Files never leave your machine</span>
        </div>
        <div className="footer-right">RIFX · Binary Patcher</div>
      </footer>

    </div>
  )
}
