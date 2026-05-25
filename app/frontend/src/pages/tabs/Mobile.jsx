import { useEffect, useState, useRef } from 'react'
import McBlock, { McSectionTitle, McSpinner, McEmpty } from '../../components/McBlock'
import McPill from '../../components/McPill'
import { ScoreBadge } from '../../components/McPill'
import { useToast } from '../../components/McToast'
import { downloadPdf } from '../../services/api'
import api from '../../services/api'

function fmt(iso) { return iso ? new Date(iso).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' }) : '—' }

export default function Mobile() {
  const [scans, setScans]         = useState([])
  const [loading, setLoading]     = useState(true)
  const [detail, setDetail]       = useState(null)
  const [url, setUrl]             = useState('')
  const [urlStatus, setUrlStatus] = useState(null)
  const [apkStatus, setApkStatus] = useState(null)
  const [dragOver, setDragOver]   = useState(false)
  const fileRef = useRef()
  const { success, error } = useToast()

  const load = async () => {
    setLoading(true)
    try { const r = await api.get('/mobile-scans/'); setScans(r.data) }
    catch { error('Erreur chargement') }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const scanFromUrl = async () => {
    if (!url) return
    setUrlStatus('loading')
    try {
      const r = await api.post('/mobile-scans/scan-url', { url })
      setUrlStatus({ ok: true, msg: `Scan lancé — ID #${r.data.id_scan}` })
      setUrl('')
      setTimeout(() => { setUrlStatus(null); load() }, 2000)
    } catch (err) {
      setUrlStatus({ ok: false, msg: err.response?.data?.detail || 'Erreur' })
    }
  }

  const uploadApk = async (file) => {
    if (!file || !file.name.endsWith('.apk')) { error('Fichier .apk requis'); return }
    setApkStatus('loading')
    const form = new FormData()
    form.append('file', file)
    try {
      const token = localStorage.getItem('cso_token')
      const res = await fetch('/mobile-scans/', { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: form })
      if (res.ok) {
        setApkStatus({ ok: true, msg: 'APK soumis — scan en cours...' })
        setTimeout(() => { setApkStatus(null); load() }, 2000)
      } else {
        const d = await res.json().catch(() => ({}))
        setApkStatus({ ok: false, msg: d.detail || 'Erreur envoi' })
      }
    } catch {
      setApkStatus({ ok: false, msg: 'Erreur réseau' })
    }
  }

  const showDetail = async (id) => {
    try { const r = await api.get(`/mobile-scans/${id}`); setDetail(r.data) }
    catch { error('Erreur') }
  }

  return (
    <div>
      <McSectionTitle actions={<button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={load}>↺</button>}>
        📱 SCAN MOBILE
      </McSectionTitle>

      {/* URL scan */}
      <McBlock>
        <div className="font-pixel text-mc-gold mb-3" style={{ fontSize: 9 }}>🔗 SCAN DEPUIS PLAY STORE</div>
        <div className="flex gap-3 items-end flex-wrap">
          <div style={{ flex: 1, minWidth: 280 }}>
            <input
              className="mc-input"
              type="url"
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder="https://play.google.com/store/apps/details?id=..."
              onKeyDown={e => e.key === 'Enter' && scanFromUrl()}
            />
          </div>
          <button className="mc-btn mc-btn-primary" onClick={scanFromUrl} disabled={urlStatus === 'loading'}>
            {urlStatus === 'loading' ? '...' : '🔍 ANALYSER'}
          </button>
        </div>
        {urlStatus && urlStatus !== 'loading' && (
          <div className="font-ui mt-2" style={{ fontSize: 12, color: urlStatus.ok ? '#3EE07A' : '#FF6666' }}>
            {urlStatus.ok ? '✅ ' : '❌ '}{urlStatus.msg}
          </div>
        )}
      </McBlock>

      {/* APK drop zone */}
      <McBlock>
        <div className="font-pixel text-mc-gold mb-3" style={{ fontSize: 9 }}>📦 UPLOAD APK DIRECT</div>
        <div
          className={`mc-dropzone ${dragOver ? 'drag-over' : ''}`}
          onClick={() => fileRef.current?.click()}
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={e => { e.preventDefault(); setDragOver(false); uploadApk(e.dataTransfer.files[0]) }}
        >
          <input ref={fileRef} type="file" accept=".apk" className="hidden" onChange={e => uploadApk(e.target.files[0])} />
          <div style={{ fontSize: 40, marginBottom: 8, position: 'relative', zIndex: 1 }}>📦</div>
          <div className="font-pixel text-mc-muted" style={{ fontSize: 8, position: 'relative', zIndex: 1 }}>
            GLISSEZ UN APK ICI OU CLIQUEZ
          </div>
          <div className="font-ui text-mc-diamond mt-2" style={{ fontSize: 12, position: 'relative', zIndex: 1 }}>
            max 200 Mo — Android uniquement
          </div>
        </div>
        {apkStatus && apkStatus !== 'loading' && (
          <div className="font-ui mt-2" style={{ fontSize: 12, color: apkStatus.ok ? '#3EE07A' : '#FF6666' }}>
            {apkStatus.ok ? '✅ ' : '❌ '}{apkStatus.msg}
          </div>
        )}
        {apkStatus === 'loading' && <div className="flex gap-2 items-center mt-2"><div className="mc-spinner" /><span className="font-ui text-mc-muted" style={{ fontSize: 12 }}>Envoi en cours...</span></div>}
      </McBlock>

      {/* Scan list */}
      <McBlock>
        {loading ? <McSpinner /> : scans.length === 0 ? <McEmpty>Aucun scan mobile</McEmpty> : (
          <div className="overflow-x-auto">
            <table className="mc-table">
              <thead><tr>{['#', 'APP', 'PACKAGE', 'SCORE', 'CRIT', 'HIGH', 'WARN', 'STATUT', 'DATE', ''].map(h => <th key={h}>{h}</th>)}</tr></thead>
              <tbody>
                {scans.map(s => (
                  <tr key={s.id_scan}>
                    <td className="font-pixel text-mc-muted" style={{ fontSize: 9 }}>{s.id_scan}</td>
                    <td><strong style={{ fontSize: 13 }}>{s.app_name || '—'}</strong></td>
                    <td className="text-mc-muted" style={{ fontSize: 11 }}>{s.package_name || '—'}</td>
                    <td><ScoreBadge score={s.security_score} /></td>
                    <td style={{ color: '#FF6666', fontFamily: 'VT323', fontSize: 22 }}>{s.critical_count || 0}</td>
                    <td style={{ color: '#FEC84B', fontFamily: 'VT323', fontSize: 22 }}>{s.high_count || 0}</td>
                    <td style={{ color: '#E3D060', fontFamily: 'VT323', fontSize: 22 }}>{s.warning_count || 0}</td>
                    <td><McPill value={s.status} /></td>
                    <td className="text-mc-muted" style={{ fontSize: 11 }}>{fmt(s.scanned_at)}</td>
                    <td>{s.status === 'completed' && <button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={() => showDetail(s.id_scan)}>DÉTAILS</button>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </McBlock>

      {detail && (
        <McBlock>
          <div className="flex items-center justify-between mb-4">
            <span className="font-pixel text-mc-diamond" style={{ fontSize: 9 }}>{detail.app_name || detail.file_name} — Score: {detail.security_score}/100</span>
            <div className="flex gap-2">
              <button className="mc-btn mc-btn-gold mc-btn-sm" onClick={() => downloadPdf(`/export/pdf/mobile-scan/${detail.id_scan}`, `mobile-${detail.id_scan}.pdf`)}>📄 PDF</button>
              <button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={() => setDetail(null)}>✕</button>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-3 mb-4">
            {[
              { val: detail.security_score ?? '?', lbl: 'SCORE', color: detail.security_score < 40 ? '#FF6666' : detail.security_score < 70 ? '#FEC84B' : '#3EE07A' },
              { val: detail.critical_count || 0, lbl: 'CRITICAL', color: '#FF6666' },
              { val: detail.high_count || 0, lbl: 'HIGH', color: '#FEC84B' },
              { val: detail.warning_count || 0, lbl: 'WARNINGS', color: '#E3D060' },
            ].map(s => (
              <div key={s.lbl} className="mc-stat">
                <div className="val" style={{ color: s.color }}>{s.val}</div>
                <div className="lbl">{s.lbl}</div>
              </div>
            ))}
          </div>

          {/* Permissions */}
          <div style={{ background: '#0A0E1A', border: '2px solid #2D3A4A', padding: 12, marginBottom: 12 }}>
            <div className="font-pixel text-mc-muted mb-3" style={{ fontSize: 8 }}>⚠️ PERMISSIONS DANGEREUSES ({(detail.dangerous_perms || []).length})</div>
            {detail.dangerous_perms?.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {detail.dangerous_perms.map((p, i) => (
                  <span key={i} className="mc-pill mc-pill-high">{typeof p === 'object' ? p.permission : p}</span>
                ))}
              </div>
            ) : <div className="text-mc-muted font-ui" style={{ fontSize: 12 }}>Aucune détectée</div>}
          </div>

          {/* Trackers */}
          <div style={{ background: '#0A0E1A', border: '2px solid #2D3A4A', padding: 12 }}>
            <div className="font-pixel text-mc-muted mb-3" style={{ fontSize: 8 }}>📡 TRACKERS ({(detail.trackers || []).length})</div>
            {detail.trackers?.length > 0 ? (
              <table className="mc-table">
                <thead><tr>{['NOM', 'CATÉGORIE'].map(h => <th key={h}>{h}</th>)}</tr></thead>
                <tbody>
                  {detail.trackers.map((t, i) => (
                    <tr key={i}>
                      <td style={{ fontSize: 13 }}>{t.name || t}</td>
                      <td className="text-mc-muted" style={{ fontSize: 12 }}>{t.category || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <div className="text-mc-muted font-ui" style={{ fontSize: 12 }}>Aucun détecté</div>}
          </div>
        </McBlock>
      )}
    </div>
  )
}
