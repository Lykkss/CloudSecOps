import { useEffect, useState } from 'react'
import McBlock, { McSectionTitle, McSpinner, McEmpty } from '../../components/McBlock'
import McPill from '../../components/McPill'
import { useToast } from '../../components/McToast'
import { downloadPdf } from '../../services/api'
import api from '../../services/api'

function fmt(iso) { return iso ? new Date(iso).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' }) : '—' }

export default function Incidents({ onAnalyzeAI }) {
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading]     = useState(true)
  const [detail, setDetail]       = useState(null)
  const [simLoading, setSimLoading] = useState(false)
  const { success, error } = useToast()

  const load = async () => {
    setLoading(true)
    try { const r = await api.get('/incidents/'); setIncidents(r.data) }
    catch { error('Erreur chargement incidents') }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const simulate = async () => {
    setSimLoading(true)
    try {
      await api.post('/incidents/simulate/iam')
      success('Compromission IAM simulée !')
      load()
    } catch (err) {
      error(err.response?.data?.detail || 'Erreur simulation')
    }
    setSimLoading(false)
  }

  const updateStatus = async (id, status) => {
    try {
      await api.patch(`/incidents/${id}/status`, { status })
      success(`Statut → ${status}`)
      load()
    } catch { error('Erreur mise à jour') }
  }

  const showDetail = async (id) => {
    try { const r = await api.get(`/incidents/${id}`); setDetail(r.data) }
    catch { error('Erreur chargement détail') }
  }

  return (
    <div>
      <McSectionTitle actions={
        <div className="flex gap-2">
          <button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={load}>↺</button>
          <button
            className="mc-btn mc-btn-danger mc-btn-sm"
            onClick={simulate}
            disabled={simLoading}
          >
            {simLoading ? '...' : '⚠️ SIMULER IAM'}
          </button>
        </div>
      }>
        ⚠️ INCIDENTS DE SÉCURITÉ
      </McSectionTitle>

      <McBlock>
        {loading ? <McSpinner /> : incidents.length === 0 ? (
          <McEmpty>Aucun incident — simulez une compromission IAM</McEmpty>
        ) : (
          <div className="overflow-x-auto">
            <table className="mc-table">
              <thead>
                <tr>{['#', 'TYPE', 'TITRE', 'SÉVÉRITÉ', 'STATUT', 'RESSOURCE', 'DATE', ''].map(h => <th key={h}>{h}</th>)}</tr>
              </thead>
              <tbody>
                {incidents.map(inc => (
                  <tr key={inc.id_incident}>
                    <td className="font-pixel text-mc-muted" style={{ fontSize: 9 }}>{inc.id_incident}</td>
                    <td className="text-mc-muted" style={{ fontSize: 12 }}>{inc.type}</td>
                    <td style={{ fontSize: 13 }}>{inc.title}</td>
                    <td><McPill value={inc.severity} /></td>
                    <td>
                      <select
                        className="mc-select"
                        style={{ fontSize: 10, padding: '4px 8px', width: 130 }}
                        value={inc.status}
                        onChange={e => updateStatus(inc.id_incident, e.target.value)}
                      >
                        {['open', 'investigating', 'resolved'].map(s => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </td>
                    <td className="text-mc-muted" style={{ fontSize: 12, maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{inc.affected_resource || '—'}</td>
                    <td className="text-mc-muted" style={{ fontSize: 12 }}>{fmt(inc.created_at)}</td>
                    <td><button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={() => showDetail(inc.id_incident)}>DÉTAILS</button></td>
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
              <button className="mc-btn mc-btn-purple mc-btn-sm" onClick={() => onAnalyzeAI?.('incident', detail.id_incident)}>🤖 IA</button>
              <button className="mc-btn mc-btn-gold mc-btn-sm" onClick={() => downloadPdf(`/export/pdf/incident/${detail.id_incident}`, `incident-${detail.id_incident}.pdf`)}>📄 PDF</button>
              <button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={() => setDetail(null)}>✕</button>
            </div>
          </div>

          <p className="font-ui text-mc-muted mb-4" style={{ fontSize: 13, lineHeight: 1.6 }}>{detail.description}</p>

          {detail.timeline?.length > 0 && (
            <div style={{ background: '#0A0E1A', border: '2px solid #2D3A4A', padding: 12, marginBottom: 12 }}>
              <div className="font-pixel text-mc-muted mb-3" style={{ fontSize: 8 }}>📅 CHRONOLOGIE</div>
              {detail.timeline.map((e, i) => (
                <div key={i} className="flex gap-3 pb-2 mb-2" style={{ borderBottom: '1px solid #1C2233' }}>
                  <span className="text-mc-muted font-ui" style={{ fontSize: 12, minWidth: 130, flexShrink: 0 }}>{fmt(e.ts)}</span>
                  <div>
                    <div className="font-ui" style={{ fontSize: 13 }}>{e.event}</div>
                    {e.detail && <div className="text-mc-muted" style={{ fontSize: 12 }}>{e.detail}</div>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {detail.ioc?.length > 0 && (
            <div style={{ background: '#0A0E1A', border: '2px solid #2D3A4A', padding: 12 }}>
              <div className="font-pixel text-mc-muted mb-3" style={{ fontSize: 8 }}>🎯 IOC</div>
              <table className="mc-table">
                <thead><tr>{['TYPE', 'VALEUR', 'CONTEXTE'].map(h => <th key={h}>{h}</th>)}</tr></thead>
                <tbody>
                  {detail.ioc.map((ioc, i) => (
                    <tr key={i}>
                      <td style={{ color: '#39D4E0', fontSize: 12, fontWeight: 600 }}>{ioc.type}</td>
                      <td><code style={{ fontSize: 11 }}>{ioc.value}</code></td>
                      <td className="text-mc-muted" style={{ fontSize: 12 }}>{ioc.context || '—'}</td>
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
