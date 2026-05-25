import { useEffect, useState } from 'react'
import McBlock, { McSectionTitle, McStat, McSpinner, McEmpty } from '../../components/McBlock'
import McPill from '../../components/McPill'
import { useToast } from '../../components/McToast'
import { downloadPdf } from '../../services/api'
import api from '../../services/api'

function fmt(iso) { return iso ? new Date(iso).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' }) : '—' }

export default function Scans({ onAnalyzeAI }) {
  const [scans, setScans] = useState([])
  const [loading, setLoading] = useState(true)
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const { success, error } = useToast()

  const load = async () => {
    setLoading(true)
    try { const r = await api.get('/scans/'); setScans(r.data) }
    catch { error('Erreur chargement scans') }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const openDetail = async (id) => {
    setDetail(null); setDetailLoading(true)
    try { const r = await api.get(`/scans/${id}`); setDetail(r.data) }
    catch { error('Erreur chargement détail') }
    setDetailLoading(false)
  }

  const sevColor = s => ({ CRITICAL: '#FF6666', HIGH: '#FEC84B', MEDIUM: '#E3D060', LOW: '#3EE07A' }[s] || '#6B7A8D')

  const totCrit = scans.reduce((a, s) => a + (s.critical_count || 0), 0)
  const totHigh = scans.reduce((a, s) => a + (s.high_count || 0), 0)
  const passed  = scans.filter(s => s.status === 'passed').length

  return (
    <div>
      <McSectionTitle actions={<button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={load}>↺ ACTUALISER</button>}>
        🔍 SCANS TRIVY CI/CD
      </McSectionTitle>

      {/* Stats */}
      {scans.length > 0 && (
        <div className="grid grid-cols-3 gap-3 mb-4">
          <McStat value={totCrit} label="CRITICAL" color="#FF6666" />
          <McStat value={totHigh} label="HIGH" color="#FEC84B" />
          <McStat value={`${passed}/${scans.length}`} label="PASSED" color="#3EE07A" />
        </div>
      )}

      <McBlock>
        {loading ? <McSpinner /> : scans.length === 0 ? (
          <McEmpty>Aucun scan — résultats après chaque push CI</McEmpty>
        ) : (
          <div className="overflow-x-auto">
            <table className="mc-table">
              <thead>
                <tr>{['#', 'IMAGE', 'TAG', 'CRIT', 'HIGH', 'MED', 'LOW', 'STATUT', 'DATE', ''].map(h => <th key={h}>{h}</th>)}</tr>
              </thead>
              <tbody>
                {scans.map(s => (
                  <tr key={s.id_scan}>
                    <td className="font-pixel text-mc-muted" style={{ fontSize: 9 }}>{s.id_scan}</td>
                    <td><code style={{ fontSize: 12, color: '#39D4E0' }}>{s.image_name}</code></td>
                    <td className="text-mc-muted" style={{ fontSize: 12 }}>{s.image_tag}</td>
                    <td style={{ color: '#FF6666', fontFamily: 'VT323', fontSize: 22 }}>{s.critical_count}</td>
                    <td style={{ color: '#FEC84B', fontFamily: 'VT323', fontSize: 22 }}>{s.high_count}</td>
                    <td style={{ color: '#E3D060', fontFamily: 'VT323', fontSize: 22 }}>{s.medium_count}</td>
                    <td style={{ color: '#3EE07A', fontFamily: 'VT323', fontSize: 22 }}>{s.low_count}</td>
                    <td><McPill value={s.status} /></td>
                    <td className="text-mc-muted" style={{ fontSize: 12 }}>{fmt(s.scanned_at)}</td>
                    <td><button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={() => openDetail(s.id_scan)}>DÉTAILS</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </McBlock>

      {/* Detail */}
      {(detail || detailLoading) && (
        <McBlock>
          <div className="flex items-center justify-between mb-4">
            <span className="font-pixel text-mc-diamond" style={{ fontSize: 9 }}>
              {detail ? `${detail.image_name}:${detail.image_tag} — ${detail.vulnerabilities?.length} CVE` : 'Chargement...'}
            </span>
            <div className="flex gap-2">
              {detail && (
                <>
                  <button className="mc-btn mc-btn-purple mc-btn-sm" onClick={() => onAnalyzeAI?.('scan', detail.id_scan)}>🤖 IA</button>
                  <button className="mc-btn mc-btn-gold mc-btn-sm" onClick={() => downloadPdf(`/export/pdf/scan/${detail.id_scan}`, `scan-${detail.id_scan}.pdf`)}>📄 PDF</button>
                </>
              )}
              <button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={() => setDetail(null)}>✕ FERMER</button>
            </div>
          </div>
          {detailLoading ? <McSpinner /> : (
            <div className="overflow-x-auto">
              <table className="mc-table">
                <thead>
                  <tr>{['CVE', 'PACKAGE', 'INSTALLÉ', 'CORRIGÉ EN', 'SÉVÉRITÉ', 'TITRE'].map(h => <th key={h}>{h}</th>)}</tr>
                </thead>
                <tbody>
                  {detail?.vulnerabilities?.map((v, i) => (
                    <tr key={i}>
                      <td><code style={{ fontSize: 11, color: '#39D4E0' }}>{v.id}</code></td>
                      <td style={{ fontSize: 13 }}>{v.package}</td>
                      <td className="text-mc-muted" style={{ fontSize: 12 }}>{v.installed_version}</td>
                      <td style={{ fontSize: 12, color: '#3EE07A' }}>{v.fixed_version || '—'}</td>
                      <td><McPill value={v.severity?.toLowerCase()} /></td>
                      <td className="text-mc-muted" style={{ fontSize: 12, maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{v.title}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </McBlock>
      )}
    </div>
  )
}
