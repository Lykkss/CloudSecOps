import { useEffect, useState } from 'react'
import McBlock, { McSectionTitle, McSpinner, McEmpty } from '../../components/McBlock'
import McPill from '../../components/McPill'
import McModal, { McField } from '../../components/McModal'
import { useToast } from '../../components/McToast'
import { downloadPdf } from '../../services/api'
import api from '../../services/api'

function fmt(iso) { return iso ? new Date(iso).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' }) : '—' }

export default function Reports() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [detail, setDetail]   = useState(null)
  const [modal, setModal]     = useState(false)
  const [form, setForm]       = useState({ title: '', id_incident: '', executive_summary: '', findings: '', recommendations: '', status: 'draft' })
  const { success, error } = useToast()

  const load = async () => {
    setLoading(true)
    try { const r = await api.get('/reports/'); setReports(r.data) }
    catch { error('Erreur chargement rapports') }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const showDetail = async (id) => {
    try { const r = await api.get(`/reports/${id}`); setDetail(r.data) }
    catch { error('Erreur') }
  }

  const finalize = async (id) => {
    try { await api.patch(`/reports/${id}/finalize`); success('Rapport finalisé'); load() }
    catch { error('Erreur finalisation') }
  }

  const parseLines = (txt, fn) => txt.trim().split('\n').filter(Boolean).map(fn)

  const submit = async (e) => {
    e.preventDefault()
    try {
      const body = {
        title: form.title,
        id_incident: form.id_incident ? parseInt(form.id_incident) : null,
        executive_summary: form.executive_summary,
        status: form.status,
        findings: parseLines(form.findings, line => {
          const p = line.split('|')
          return { severity: p[0]?.trim(), title: p[1]?.trim() || '', description: p.slice(2).join('|').trim() }
        }),
        recommendations: parseLines(form.recommendations, line => {
          const p = line.split('|')
          return { priority: p[0]?.trim(), action: p[1]?.trim() || '', owner: p[2]?.trim() || null }
        }),
      }
      await api.post('/reports/', body)
      success('Rapport créé !')
      setModal(false)
      setForm({ title: '', id_incident: '', executive_summary: '', findings: '', recommendations: '', status: 'draft' })
      load()
    } catch (err) {
      error(err.response?.data?.detail || 'Erreur création')
    }
  }

  const sevClass = sev => ({ immediate: 'critical', short_term: 'high', long_term: 'low' }[sev] || 'medium')

  return (
    <div>
      <McSectionTitle actions={
        <div className="flex gap-2">
          <button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={load}>↺</button>
          <button className="mc-btn mc-btn-primary mc-btn-sm" onClick={() => setModal(true)}>+ RAPPORT</button>
        </div>
      }>
        📜 RAPPORTS FORENSIQUES
      </McSectionTitle>

      <McBlock>
        {loading ? <McSpinner /> : reports.length === 0 ? <McEmpty>Aucun rapport forensique</McEmpty> : (
          <div className="overflow-x-auto">
            <table className="mc-table">
              <thead><tr>{['#', 'TITRE', 'STATUT', 'INCIDENT', 'DATE', ''].map(h => <th key={h}>{h}</th>)}</tr></thead>
              <tbody>
                {reports.map(r => (
                  <tr key={r.id_report}>
                    <td className="font-pixel text-mc-muted" style={{ fontSize: 9 }}>{r.id_report}</td>
                    <td style={{ fontSize: 13 }}>{r.title}</td>
                    <td><McPill value={r.status} /></td>
                    <td className="text-mc-muted" style={{ fontSize: 12 }}>{r.id_incident ? `#${r.id_incident}` : '—'}</td>
                    <td className="text-mc-muted" style={{ fontSize: 12 }}>{fmt(r.created_at)}</td>
                    <td>
                      <div className="flex gap-2">
                        <button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={() => showDetail(r.id_report)}>LIRE</button>
                        {r.status === 'draft' && <button className="mc-btn mc-btn-accent mc-btn-sm" onClick={() => finalize(r.id_report)}>FINAL</button>}
                      </div>
                    </td>
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
            <span className="font-pixel text-mc-diamond" style={{ fontSize: 9 }}>{detail.title}</span>
            <div className="flex gap-2">
              <button className="mc-btn mc-btn-gold mc-btn-sm" onClick={() => downloadPdf(`/export/pdf/report/${detail.id_report}`, `report-${detail.id_report}.pdf`)}>📄 PDF</button>
              <button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={() => setDetail(null)}>✕</button>
            </div>
          </div>

          <div style={{ background: '#0A0E1A', border: '2px solid #2D3A4A', padding: 12, marginBottom: 12 }}>
            <div className="font-pixel text-mc-muted mb-2" style={{ fontSize: 8 }}>📋 RÉSUMÉ EXÉCUTIF</div>
            <p className="font-ui text-mc-light" style={{ fontSize: 13, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{detail.executive_summary}</p>
          </div>

          {detail.findings?.length > 0 && (
            <div style={{ background: '#0A0E1A', border: '2px solid #2D3A4A', padding: 12, marginBottom: 12 }}>
              <div className="font-pixel text-mc-muted mb-3" style={{ fontSize: 8 }}>🔎 CONSTATATIONS</div>
              {detail.findings.map((f, i) => (
                <div key={i} className="pb-2 mb-2" style={{ borderBottom: '1px solid #1C2233' }}>
                  <div className="flex items-center gap-2 mb-1">
                    <McPill value={f.severity?.toLowerCase()} />
                    <strong className="font-ui" style={{ fontSize: 13 }}>{f.title}</strong>
                  </div>
                  <p className="text-mc-muted font-ui" style={{ fontSize: 12 }}>{f.description}</p>
                </div>
              ))}
            </div>
          )}

          {detail.recommendations?.length > 0 && (
            <div style={{ background: '#0A0E1A', border: '2px solid #2D3A4A', padding: 12 }}>
              <div className="font-pixel text-mc-muted mb-3" style={{ fontSize: 8 }}>💡 RECOMMANDATIONS</div>
              {detail.recommendations.map((rec, i) => (
                <div key={i} className="flex gap-3 pb-2 mb-2" style={{ borderBottom: '1px solid #1C2233' }}>
                  <McPill value={sevClass(rec.priority)} />
                  <div>
                    <div className="font-ui" style={{ fontSize: 13 }}>{rec.action}</div>
                    {rec.owner && <div className="text-mc-muted" style={{ fontSize: 12 }}>→ {rec.owner}</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </McBlock>
      )}

      <McModal open={modal} onClose={() => setModal(false)} title="📜 NOUVEAU RAPPORT FORENSIQUE">
        <form onSubmit={submit}>
          <McField label="TITRE *">
            <input className="mc-input" value={form.title} onChange={e => setForm(f => ({...f, title: e.target.value}))} placeholder="Rapport investigation IAM" required />
          </McField>
          <McField label="INCIDENT LIÉ (ID, optionnel)">
            <input className="mc-input" type="number" value={form.id_incident} onChange={e => setForm(f => ({...f, id_incident: e.target.value}))} placeholder="ex: 1" />
          </McField>
          <McField label="RÉSUMÉ EXÉCUTIF *">
            <textarea className="mc-input" rows={3} value={form.executive_summary} onChange={e => setForm(f => ({...f, executive_summary: e.target.value}))} placeholder="Résumé..." required />
          </McField>
          <McField label="CONSTATATIONS (SEVERITY|Titre|Description par ligne)">
            <textarea className="mc-input" rows={4} value={form.findings} onChange={e => setForm(f => ({...f, findings: e.target.value}))} placeholder="CRITICAL|Clé IAM exposée|Trouvée sur GitHub" />
          </McField>
          <McField label="RECOMMANDATIONS (PRIORITY|Action|Responsable par ligne)">
            <textarea className="mc-input" rows={3} value={form.recommendations} onChange={e => setForm(f => ({...f, recommendations: e.target.value}))} placeholder="immediate|Révoquer les clés|SecOps" />
          </McField>
          <McField label="STATUT">
            <select className="mc-select" value={form.status} onChange={e => setForm(f => ({...f, status: e.target.value}))}>
              <option value="draft">Brouillon</option>
              <option value="final">Final</option>
            </select>
          </McField>
          <div className="flex gap-3 justify-end mt-4">
            <button type="button" className="mc-btn mc-btn-ghost" onClick={() => setModal(false)}>ANNULER</button>
            <button type="submit" className="mc-btn mc-btn-primary">CRÉER</button>
          </div>
        </form>
      </McModal>
    </div>
  )
}
