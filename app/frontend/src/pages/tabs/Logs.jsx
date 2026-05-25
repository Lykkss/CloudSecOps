import { useEffect, useState } from 'react'
import McBlock, { McSectionTitle, McSpinner, McEmpty } from '../../components/McBlock'
import { useToast } from '../../components/McToast'
import api from '../../services/api'

export default function Logs() {
  const [groups, setGroups]           = useState([])
  const [allGroups, setAllGroups]     = useState([])
  const [loading, setLoading]         = useState(true)
  const [selected, setSelected]       = useState(null)
  const [streams, setStreams]         = useState([])
  const [events, setEvents]           = useState(null)
  const [streamsLoading, setStreamsLoading] = useState(false)
  const [eventsLoading, setEventsLoading]  = useState(false)
  const [search, setSearch]           = useState('')
  const { error } = useToast()

  const loadGroups = async () => {
    setLoading(true)
    try {
      const r = await api.get('/logs/cloudwatch/groups')
      setAllGroups(r.data)
      setGroups(r.data)
    } catch { error('Erreur chargement logs') }
    setLoading(false)
  }

  useEffect(() => { loadGroups() }, [])

  const filterGroups = (q) => {
    setSearch(q)
    if (!q) { setGroups(allGroups); return }
    setGroups(allGroups.filter(g => (g.logGroupName || g).toLowerCase().includes(q.toLowerCase())))
  }

  const selectGroup = async (name) => {
    setSelected(name)
    setStreams([])
    setEvents(null)
    setStreamsLoading(true)
    try {
      const r = await api.get(`/logs/cloudwatch/groups/${encodeURIComponent(name)}/streams`)
      setStreams(r.data)
    } catch { error('Erreur chargement streams') }
    setStreamsLoading(false)
  }

  const loadEvents = async (groupName, streamName) => {
    setEvents(null)
    setEventsLoading(true)
    try {
      const r = await api.get(`/logs/cloudwatch/groups/${encodeURIComponent(groupName)}/streams/${encodeURIComponent(streamName)}/events?limit=100`)
      setEvents({ stream: streamName, data: r.data })
    } catch { error('Erreur chargement events') }
    setEventsLoading(false)
  }

  const fmtTs = ts => ts ? new Date(ts).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'medium' }) : ''

  return (
    <div>
      <McSectionTitle actions={<button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={loadGroups}>↺</button>}>
        📡 LOGS CLOUDWATCH AWS
      </McSectionTitle>

      <McBlock style={{ padding: 0 }}>
        <div className="flex" style={{ minHeight: 520 }}>
          {/* Left panel — log groups */}
          <div style={{ width: 260, borderRight: '2px solid #2D3A4A', flexShrink: 0 }}>
            <div style={{ padding: '12px 12px 8px', borderBottom: '1px solid #2D3A4A' }}>
              <input
                className="mc-input"
                value={search}
                onChange={e => filterGroups(e.target.value)}
                placeholder="Filtrer les groupes..."
                style={{ fontSize: 12, padding: '6px 10px' }}
              />
            </div>
            <div style={{ overflowY: 'auto', maxHeight: 470 }}>
              {loading ? (
                <div style={{ padding: 16 }}><McSpinner /></div>
              ) : groups.length === 0 ? (
                <div className="font-ui text-mc-muted" style={{ padding: 16, fontSize: 12 }}>Aucun groupe</div>
              ) : groups.map(g => {
                const name = g.logGroupName || g
                return (
                  <div
                    key={name}
                    onClick={() => selectGroup(name)}
                    style={{
                      padding: '8px 12px',
                      borderBottom: '1px solid #1C2233',
                      cursor: 'pointer',
                      fontSize: 11,
                      fontFamily: 'Share Tech Mono, monospace',
                      color: selected === name ? '#39D4E0' : '#6B7A8D',
                      background: selected === name ? '#0F1F3A' : 'transparent',
                      wordBreak: 'break-all',
                      transition: 'background 0.1s',
                    }}
                  >
                    {selected === name && <span style={{ color: '#39D4E0', marginRight: 4 }}>▶</span>}
                    {name}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Right panel */}
          <div style={{ flex: 1, overflowY: 'auto', maxHeight: 520 }}>
            {!selected && (
              <div className="flex flex-col items-center justify-center h-full gap-3" style={{ padding: 32, color: '#6B7A8D' }}>
                <span style={{ fontSize: 36 }}>📡</span>
                <span className="font-pixel" style={{ fontSize: 8 }}>SÉLECTIONNEZ UN GROUPE DE LOGS</span>
              </div>
            )}

            {selected && !events && (
              <div style={{ padding: 12 }}>
                <div className="font-pixel text-mc-diamond mb-3" style={{ fontSize: 8 }}>
                  {selected}
                </div>
                {streamsLoading ? <McSpinner /> : streams.length === 0 ? (
                  <div className="font-ui text-mc-muted" style={{ fontSize: 12 }}>Aucun stream</div>
                ) : streams.map(s => {
                  const name = s.logStreamName || s
                  return (
                    <div
                      key={name}
                      onClick={() => loadEvents(selected, name)}
                      style={{
                        padding: '8px 12px',
                        borderBottom: '1px solid #1C2233',
                        cursor: 'pointer',
                        fontSize: 12,
                        fontFamily: 'Share Tech Mono, monospace',
                        color: '#E6EDF3',
                        transition: 'background 0.1s',
                      }}
                      onMouseEnter={e => e.currentTarget.style.background = '#1C2233'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                      📋 {name}
                    </div>
                  )
                })}
              </div>
            )}

            {events && (
              <div style={{ padding: 12 }}>
                <div className="flex items-center gap-3 mb-3 flex-wrap">
                  <button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={() => setEvents(null)}>← RETOUR</button>
                  <span className="font-pixel text-mc-muted" style={{ fontSize: 7 }}>{events.stream} — {events.data.length} événements</span>
                  <button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={() => loadEvents(selected, events.stream)}>↺</button>
                </div>
                {eventsLoading ? <McSpinner /> : (
                  <div className="mc-log-pane" style={{ maxHeight: 420 }}>
                    {events.data.map((e, i) => (
                      <div key={i} style={{ padding: '2px 0', borderBottom: '1px solid #0D1220' }}>
                        <span style={{ color: '#6B7A8D', marginRight: 12, fontSize: 14 }}>{fmtTs(e.timestamp)}</span>
                        <span style={{ fontSize: 15 }}>{e.message || e}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </McBlock>
    </div>
  )
}
