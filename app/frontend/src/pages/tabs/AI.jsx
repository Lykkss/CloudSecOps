import { useEffect, useState, useRef } from 'react'
import McBlock, { McSectionTitle, McSpinner } from '../../components/McBlock'
import api from '../../services/api'

export default function AI({ pendingAnalyze, onAnalyzeDone }) {
  const [status, setStatus]       = useState(null)
  const [models, setModels]       = useState([])
  const [model, setModel]         = useState('')
  const [contextType, setContextType] = useState('')
  const [contextId, setContextId]   = useState('')
  const [scans, setScans]         = useState([])
  const [incidents, setIncidents] = useState([])
  const [messages, setMessages]   = useState([])
  const [input, setInput]         = useState('')
  const [streaming, setStreaming] = useState(false)
  const chatRef = useRef()
  const historyRef = useRef([])

  const checkStatus = async () => {
    try {
      const r = await api.get('/ai/status')
      setStatus(r.data.available)
      setModels(r.data.models || [])
    } catch { setStatus(false) }
  }

  const loadContext = async () => {
    try {
      const [s, i] = await Promise.all([api.get('/scans/'), api.get('/incidents/')])
      setScans(s.data)
      setIncidents(i.data)
    } catch {}
  }

  useEffect(() => {
    checkStatus()
    loadContext()
  }, [])

  // Handle analyze from other tabs
  useEffect(() => {
    if (pendingAnalyze) {
      const { type, id } = pendingAnalyze
      streamAnalyze(`/ai/analyze/${type}/${id}`, `Analyse ${type} #${id}`)
      onAnalyzeDone?.()
    }
  }, [pendingAnalyze])

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight
  }, [messages])

  const appendMsg = (role, content, streaming = false) => {
    const id = Date.now() + Math.random()
    setMessages(m => [...m, { id, role, content, streaming }])
    return id
  }

  const updateMsg = (id, content, done = false) => {
    setMessages(m => m.map(msg => msg.id === id ? { ...msg, content, streaming: !done } : msg))
  }

  const sendChat = async () => {
    if (streaming || !input.trim()) return
    const msg = input.trim()
    setInput('')

    historyRef.current.push({ role: 'user', content: msg })
    appendMsg('user', msg)

    let ctxType, ctxId
    if (contextType && contextId) { ctxType = contextType; ctxId = parseInt(contextId) }

    await streamChat({
      messages: historyRef.current,
      model: model || undefined,
      context_type: ctxType,
      context_id: ctxId,
    })
  }

  const streamChat = async (body) => {
    setStreaming(true)
    const msgId = appendMsg('assistant', '', true)
    let accumulated = ''

    try {
      const token = localStorage.getItem('cso_token')
      const res = await fetch('/ai/chat', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const d = await res.json().catch(() => ({ detail: 'Erreur' }))
        updateMsg(msgId, d.detail || 'Erreur API', true)
        setStreaming(false)
        return
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (data === '[DONE]') { updateMsg(msgId, accumulated, true); break }
          try { const obj = JSON.parse(data); if (obj.token) { accumulated += obj.token; updateMsg(msgId, accumulated, false) } } catch {}
        }
      }
      updateMsg(msgId, accumulated || '(pas de réponse)', true)
      historyRef.current.push({ role: 'assistant', content: accumulated })
    } catch (err) {
      updateMsg(msgId, `Erreur : ${err.message}`, true)
    }
    setStreaming(false)
  }

  const streamAnalyze = async (endpoint, label) => {
    setStreaming(true)
    appendMsg('user', `⚡ Analyse : ${label}`)
    const msgId = appendMsg('assistant', '', true)
    let accumulated = ''

    try {
      const token = localStorage.getItem('cso_token')
      const res = await fetch(endpoint, { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
      if (!res.ok) { const d = await res.json().catch(() => ({})); updateMsg(msgId, d.detail || 'Erreur', true); setStreaming(false); return }
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (data === '[DONE]') { updateMsg(msgId, accumulated, true); break }
          try { const obj = JSON.parse(data); if (obj.token) { accumulated += obj.token; updateMsg(msgId, accumulated, false) } } catch {}
        }
      }
      updateMsg(msgId, accumulated || '(vide)', true)
    } catch (err) { updateMsg(msgId, `Erreur : ${err.message}`, true) }
    setStreaming(false)
  }

  const clearChat = () => { setMessages([]); historyRef.current = [] }

  return (
    <div>
      <McSectionTitle>🤖 ASSISTANT IA — OLLAMA</McSectionTitle>

      {/* Status bar */}
      <McBlock>
        <div className="flex items-center gap-3 flex-wrap">
          <div style={{ width: 10, height: 10, background: status === null ? '#FEC84B' : status ? '#3EE07A' : '#FF3333', imageRendering: 'pixelated', animation: status ? 'torch 0.2s steps(2) infinite' : undefined }} />
          <span className="font-pixel" style={{ fontSize: 9, color: status === null ? '#FEC84B' : status ? '#3EE07A' : '#FF3333' }}>
            {status === null ? 'VÉRIFICATION...' : status ? `OLLAMA ACTIF — ${models.length} MODÈLE(S)` : 'OLLAMA HORS LIGNE'}
          </span>
          <button className="mc-btn mc-btn-ghost mc-btn-sm ml-auto" onClick={checkStatus}>↺</button>
        </div>

        {status && (
          <div className="flex gap-3 flex-wrap mt-4">
            <div>
              <label className="block font-pixel text-mc-muted mb-1" style={{ fontSize: 7 }}>MODÈLE</label>
              <select className="mc-select" style={{ fontSize: 12, padding: '4px 8px' }} value={model} onChange={e => setModel(e.target.value)}>
                <option value="">Défaut</option>
                {models.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div>
              <label className="block font-pixel text-mc-muted mb-1" style={{ fontSize: 7 }}>CONTEXTE</label>
              <select className="mc-select" style={{ fontSize: 12, padding: '4px 8px', minWidth: 200 }} value={contextType} onChange={e => setContextType(e.target.value)}>
                <option value="">Sans contexte</option>
                <option disabled>── Scans ──</option>
                {scans.map(s => <option key={`scan-${s.id_scan}`} value="scan" onClick={() => setContextId(s.id_scan)}>Scan #{s.id_scan} — {s.image_name}</option>)}
                <option disabled>── Incidents ──</option>
                {incidents.map(i => <option key={`inc-${i.id_incident}`} value="incident" onClick={() => setContextId(i.id_incident)}>Incident #{i.id_incident} — {i.title}</option>)}
              </select>
            </div>
            <div>
              <label className="block font-pixel text-mc-muted mb-1" style={{ fontSize: 7 }}>ID CONTEXTE</label>
              <input className="mc-input" type="number" value={contextId} onChange={e => setContextId(e.target.value)} style={{ width: 80, fontSize: 12, padding: '4px 8px' }} placeholder="ex: 1" />
            </div>
            <button className="mc-btn mc-btn-ghost mc-btn-sm" style={{ alignSelf: 'flex-end' }} onClick={clearChat}>🗑 VIDER</button>
          </div>
        )}
      </McBlock>

      {/* Chat */}
      <McBlock style={{ padding: 0 }}>
        {/* Messages */}
        <div
          ref={chatRef}
          style={{
            height: 440,
            overflowY: 'auto',
            padding: 16,
            background: '#050810',
            borderBottom: '2px solid #2D3A4A',
          }}
        >
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full gap-3">
              <div style={{ fontSize: 48 }}>🤖</div>
              <div className="font-pixel text-mc-muted" style={{ fontSize: 8, textAlign: 'center' }}>
                POSEZ UNE QUESTION À L'ASSISTANT IA<br />
                <span style={{ color: '#39D4E0' }}>LLAMA3 VIA OLLAMA SUR KIMSUFI</span>
              </div>
            </div>
          )}
          {messages.map(msg => (
            <div key={msg.id} className={`mb-4 ${msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'}`}>
              <div>
                <div className="font-pixel mb-1" style={{ fontSize: 7, color: '#6B7A8D', textAlign: msg.role === 'user' ? 'right' : 'left' }}>
                  {msg.role === 'user' ? 'VOUS' : '🤖 IA'}
                </div>
                <div className={msg.role === 'user' ? 'mc-bubble-user' : 'mc-bubble-ai'}>
                  {msg.content}
                  {msg.streaming && <span className="streaming-cursor" />}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Input */}
        <div className="flex gap-3 p-3" style={{ background: '#1C2233' }}>
          <input
            className="mc-input flex-1"
            placeholder={status ? 'Posez votre question...' : 'Ollama hors ligne'}
            value={input}
            disabled={!status || streaming}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendChat()}
          />
          <button
            className="mc-btn mc-btn-accent"
            disabled={!status || streaming}
            onClick={sendChat}
          >
            {streaming ? '...' : '▶ ENVOYER'}
          </button>
        </div>
      </McBlock>
    </div>
  )
}
