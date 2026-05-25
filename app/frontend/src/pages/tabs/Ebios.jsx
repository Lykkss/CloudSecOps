import { useEffect, useState } from 'react'
import McBlock, { McSectionTitle, McSpinner, McEmpty } from '../../components/McBlock'
import McModal, { McField } from '../../components/McModal'
import { RiskPill } from '../../components/McPill'
import { useToast } from '../../components/McToast'
import { downloadPdf } from '../../services/api'
import api from '../../services/api'

function fmt(iso) { return iso ? new Date(iso).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' }) : '—' }
const gravClass = g => g >= 4 ? 'mc-pill-critical' : g >= 3 ? 'mc-pill-high' : g >= 2 ? 'mc-pill-medium' : 'mc-pill-low'
const riskColor = (l, g) => { const v = l * g; return v >= 12 ? 'mc-risk-vhigh' : v >= 6 ? 'mc-risk-high' : v >= 3 ? 'mc-risk-med' : 'mc-risk-low' }

function RiskMatrix({ scenarios }) {
  const cells = {}
  scenarios.forEach(sc => { const k = `${sc.likelihood}-${sc.gravity}`; cells[k] = (cells[k] || 0) + 1 })
  return (
    <div>
      <div className="font-pixel text-mc-muted mb-2" style={{ fontSize: 7 }}>VRAISEMBLANCE / GRAVITÉ</div>
      <div style={{ display: 'grid', gridTemplateColumns: '24px repeat(4, 1fr)', gap: 2, fontSize: 10 }}>
        <div />
        {[1,2,3,4].map(l => <div key={l} className="text-center font-pixel text-mc-muted" style={{ fontSize: 7, padding: '4px 0' }}>V{l}</div>)}
        {[4,3,2,1].map(g => (
          <>
            <div key={`g${g}`} className="font-pixel text-mc-muted flex items-center justify-center" style={{ fontSize: 7 }}>G{g}</div>
            {[1,2,3,4].map(l => {
              const k = `${l}-${g}`; const cnt = cells[k] || 0
              return (
                <div key={k} className={`${riskColor(l,g)} text-center font-pixel`} style={{ padding: '6px 4px', fontSize: 9, fontWeight: 700 }}>
                  {cnt || ''}
                </div>
              )
            })}
          </>
        ))}
      </div>
    </div>
  )
}

function EbiosProjectDetail({ project }) {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)
  const [open, setOpen]     = useState({})
  const { success, error }  = useToast()

  const load = async () => {
    setLoading(true)
    try { const r = await api.get(`/ebios/${project.id_project}`); setData(r.data) }
    catch { error('Erreur chargement projet EBIOS') }
    setLoading(false)
  }

  useEffect(() => { load() }, [project.id_project])

  const addItem = async (path, body, msg) => {
    try { await api.post(path, body); success(msg); load() }
    catch (err) { error(err.response?.data?.detail || 'Erreur') }
  }

  const toggleSection = (s) => setOpen(o => ({ ...o, [s]: !o[s] }))

  if (loading) return <McSpinner />

  const assetOpts = (data?.assets || []).map(a => ({ value: a.id_asset, label: a.name }))

  return (
    <div>
      <div className="flex gap-2 mb-4 flex-wrap">
        {data?.status !== 'completed' && (
          <button className="mc-btn mc-btn-accent mc-btn-sm" onClick={async () => {
            try { await api.patch(`/ebios/${project.id_project}/complete`); success('Projet finalisé'); load() }
            catch { error('Erreur') }
          }}>✔ FINALISER</button>
        )}
        <button className="mc-btn mc-btn-gold mc-btn-sm" onClick={() => downloadPdf(`/export/pdf/ebios/${project.id_project}`, `ebios-${project.id_project}.pdf`)}>📄 PDF</button>
      </div>

      {/* Atelier 1 — Actifs */}
      <Section title={`🏗️ ACTIFS (${data?.assets?.length || 0})`} open={open.assets} onToggle={() => toggleSection('assets')}>
        <AddForm fields={[
          { id: 'name', label: 'NOM *', placeholder: 'Serveur web' },
          { id: 'type', label: 'TYPE', type: 'select', options: ['', 'process', 'information', 'system'] }
        ]} onAdd={vals => addItem(`/ebios/${project.id_project}/assets`, { name: vals.name, type: vals.type || undefined }, 'Actif ajouté')} />
        {data?.assets?.map(a => (
          <div key={a.id_asset} className="flex justify-between py-2 font-ui" style={{ fontSize: 13, borderBottom: '1px solid #1C2233' }}>
            <strong>{a.name}</strong>
            <span className="mc-pill mc-pill-draft">{a.type || '—'}</span>
          </div>
        ))}
        {!data?.assets?.length && <div className="text-mc-muted font-ui" style={{ fontSize: 12 }}>Aucun actif</div>}
      </Section>

      {/* Atelier 1 — Événements redoutés */}
      <Section title={`😨 ÉVÉNEMENTS REDOUTÉS (${data?.fear_events?.length || 0})`} open={open.fears} onToggle={() => toggleSection('fears')}>
        <AddForm fields={[
          { id: 'id_asset', label: 'ACTIF LIÉ', type: 'select', options: assetOpts },
          { id: 'description', label: 'DESCRIPTION *', placeholder: 'Divulgation données' },
          { id: 'gravity', label: 'GRAVITÉ (1-4)', type: 'number', min: 1, max: 4, style: { width: 70 } },
        ]} onAdd={vals => addItem(`/ebios/${project.id_project}/fear-events`, {
          id_asset: vals.id_asset ? parseInt(vals.id_asset) : undefined,
          description: vals.description,
          gravity: vals.gravity ? parseInt(vals.gravity) : undefined,
        }, 'Événement ajouté')} />
        {data?.fear_events?.map(f => (
          <div key={f.id_event} className="flex justify-between py-2 font-ui" style={{ fontSize: 13, borderBottom: '1px solid #1C2233' }}>
            <span>{f.description}</span>
            {f.gravity && <span className={`mc-pill ${gravClass(f.gravity)}`}>G{f.gravity}</span>}
          </div>
        ))}
        {!data?.fear_events?.length && <div className="text-mc-muted font-ui" style={{ fontSize: 12 }}>Aucun événement redouté</div>}
      </Section>

      {/* Atelier 2 — Sources de risque */}
      <Section title={`☠️ SOURCES DE RISQUE (${data?.risk_sources?.length || 0})`} open={open.sources} onToggle={() => toggleSection('sources')}>
        <AddForm fields={[
          { id: 'name', label: 'NOM *', placeholder: 'Cybercriminel' },
          { id: 'pertinence', label: 'PERTINENCE (1-4)', type: 'number', min: 1, max: 4, style: { width: 70 } },
        ]} onAdd={vals => addItem(`/ebios/${project.id_project}/risk-sources`, {
          name: vals.name,
          pertinence: vals.pertinence ? parseInt(vals.pertinence) : undefined,
        }, 'Source ajoutée')} />
        {data?.risk_sources?.map(s => (
          <div key={s.id_source} className="flex justify-between py-2 font-ui" style={{ fontSize: 13, borderBottom: '1px solid #1C2233' }}>
            <strong>{s.name}</strong>
            {s.pertinence && <span className={`mc-pill ${gravClass(s.pertinence)}`}>P{s.pertinence}</span>}
          </div>
        ))}
        {!data?.risk_sources?.length && <div className="text-mc-muted font-ui" style={{ fontSize: 12 }}>Aucune source</div>}
      </Section>

      {/* Ateliers 3&4 — Scénarios */}
      <Section title={`⚔️ SCÉNARIOS (${data?.scenarios?.length || 0})`} open={open.scenarios} onToggle={() => toggleSection('scenarios')}>
        <AddForm fields={[
          { id: 'title', label: 'TITRE *', placeholder: 'Exfiltration via phishing' },
          { id: 'likelihood', label: 'VRAISEMBLANCE (1-4)', type: 'number', min: 1, max: 4, style: { width: 70 } },
          { id: 'gravity', label: 'GRAVITÉ (1-4)', type: 'number', min: 1, max: 4, style: { width: 70 } },
          { id: 'treatment', label: 'TRAITEMENT', type: 'select', options: [
            { value: 'reduce', label: 'Réduire' },
            { value: 'accept', label: 'Accepter' },
            { value: 'transfer', label: 'Transférer' },
            { value: 'avoid', label: 'Éviter' },
          ]},
        ]} onAdd={vals => addItem(`/ebios/${project.id_project}/scenarios`, {
          type: 'strategic',
          title: vals.title,
          likelihood: parseInt(vals.likelihood) || 1,
          gravity: parseInt(vals.gravity) || 1,
          treatment: vals.treatment || 'reduce',
        }, 'Scénario ajouté')} />
        {data?.scenarios?.map(sc => {
          const rl = (sc.likelihood || 0) * (sc.gravity || 0)
          return (
            <div key={sc.id_scenario} className="py-2" style={{ borderBottom: '1px solid #1C2233' }}>
              <div className="flex justify-between items-center">
                <strong className="font-ui" style={{ fontSize: 13 }}>{sc.title}</strong>
                <RiskPill level={rl} />
              </div>
              <div className="text-mc-muted font-ui mt-1" style={{ fontSize: 11 }}>
                V:{sc.likelihood} G:{sc.gravity} — {sc.treatment}
              </div>
            </div>
          )
        })}
        {!data?.scenarios?.length && <div className="text-mc-muted font-ui" style={{ fontSize: 12 }}>Aucun scénario</div>}
      </Section>

      {/* Matrice */}
      {data?.scenarios?.length > 0 && (
        <div style={{ background: '#0A0E1A', border: '2px solid #2D3A4A', padding: 12, marginTop: 8 }}>
          <div className="font-pixel text-mc-muted mb-3" style={{ fontSize: 8 }}>📊 MATRICE DE RISQUE</div>
          <RiskMatrix scenarios={data.scenarios} />
        </div>
      )}
    </div>
  )
}

function Section({ title, open, onToggle, children }) {
  return (
    <div className="mc-ebios-project mb-2">
      <div className="mc-ebios-header" onClick={onToggle}>
        <span>{title}</span>
        <span style={{ color: '#6B7A8D' }}>{open ? '▲' : '▼'}</span>
      </div>
      {open && <div style={{ padding: 12 }}>{children}</div>}
    </div>
  )
}

function AddForm({ fields, onAdd }) {
  const [vals, setVals] = useState({})
  const set = (k, v) => setVals(prev => ({ ...prev, [k]: v }))
  const submit = (e) => { e.preventDefault(); onAdd(vals); setVals({}) }

  return (
    <form onSubmit={submit} className="flex flex-wrap gap-2 items-end mb-3 p-2" style={{ background: '#0A0E1A', border: '1px solid #2D3A4A' }}>
      {fields.map(f => (
        <div key={f.id} className="flex flex-col" style={f.style}>
          <label className="font-pixel text-mc-muted mb-1" style={{ fontSize: 7 }}>{f.label}</label>
          {f.type === 'select' ? (
            <select className="mc-select" style={{ fontSize: 12, padding: '4px 8px', ...f.style }} value={vals[f.id] || ''} onChange={e => set(f.id, e.target.value)}>
              {f.options.map(o => typeof o === 'string'
                ? <option key={o} value={o}>{o || '—'}</option>
                : <option key={o.value} value={o.value}>{o.label}</option>
              )}
            </select>
          ) : (
            <input
              className="mc-input"
              type={f.type || 'text'}
              placeholder={f.placeholder}
              min={f.min} max={f.max}
              style={{ fontSize: 12, padding: '4px 8px', ...f.style }}
              value={vals[f.id] || ''}
              onChange={e => set(f.id, e.target.value)}
            />
          )}
        </div>
      ))}
      <button type="submit" className="mc-btn mc-btn-primary mc-btn-sm" style={{ alignSelf: 'flex-end' }}>+</button>
    </form>
  )
}

export default function Ebios() {
  const [projects, setProjects]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [modal, setModal]         = useState(false)
  const [expanded, setExpanded]   = useState(null)
  const [form, setForm]           = useState({ name: '', scope: '', context: '' })
  const { success, error }        = useToast()

  const load = async () => {
    setLoading(true)
    try { const r = await api.get('/ebios/'); setProjects(r.data) }
    catch { error('Erreur') }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const create = async (e) => {
    e.preventDefault()
    try {
      await api.post('/ebios/', { name: form.name, scope: form.scope || undefined, context: form.context || undefined })
      success('Projet EBIOS créé !')
      setModal(false)
      setForm({ name: '', scope: '', context: '' })
      load()
    } catch (err) {
      error(err.response?.data?.detail || 'Erreur')
    }
  }

  return (
    <div>
      <McSectionTitle actions={<button className="mc-btn mc-btn-primary mc-btn-sm" onClick={() => setModal(true)}>+ PROJET</button>}>
        🛡️ EBIOS RISK MANAGER
      </McSectionTitle>

      {loading ? <McSpinner /> : projects.length === 0 ? (
        <McBlock><McEmpty>Aucun projet EBIOS RM</McEmpty></McBlock>
      ) : projects.map(p => (
        <div key={p.id_project} className="mc-ebios-project mb-3">
          <div className="mc-ebios-header" onClick={() => setExpanded(expanded === p.id_project ? null : p.id_project)}>
            <div className="flex items-center gap-3">
              <span style={{ fontSize: 9 }}>{p.name}</span>
              <span className={`mc-pill mc-pill-${p.status || 'in_progress'}`}>{p.status || 'en cours'}</span>
            </div>
            <span className="text-mc-muted font-ui" style={{ fontSize: 11 }}>{fmt(p.created_at)}</span>
          </div>
          {expanded === p.id_project && (
            <div style={{ padding: 12 }}>
              <EbiosProjectDetail project={p} />
            </div>
          )}
        </div>
      ))}

      <McModal open={modal} onClose={() => setModal(false)} title="🛡️ NOUVEAU PROJET EBIOS RM">
        <form onSubmit={create}>
          <McField label="NOM DU PROJET *">
            <input className="mc-input" value={form.name} onChange={e => setForm(f => ({...f, name: e.target.value}))} placeholder="Analyse de risques SI Prod" required />
          </McField>
          <McField label="PÉRIMÈTRE">
            <textarea className="mc-input" rows={2} value={form.scope} onChange={e => setForm(f => ({...f, scope: e.target.value}))} placeholder="Systèmes concernés..." />
          </McField>
          <McField label="CONTEXTE">
            <textarea className="mc-input" rows={2} value={form.context} onChange={e => setForm(f => ({...f, context: e.target.value}))} placeholder="Secteur d'activité..." />
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
