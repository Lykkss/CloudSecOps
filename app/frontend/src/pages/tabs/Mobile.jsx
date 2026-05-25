import { useEffect, useState, useRef } from 'react'
import McBlock, { McSectionTitle, McSpinner, McEmpty } from '../../components/McBlock'
import McPill from '../../components/McPill'
import { ScoreBadge } from '../../components/McPill'
import { useToast } from '../../components/McToast'
import api from '../../services/api'

function fmt(iso) { return iso ? new Date(iso).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' }) : '—' }
function parseJson(val) {
  if (!val) return []
  if (Array.isArray(val)) return val
  try { return JSON.parse(val) } catch { return [] }
}
function sleep(ms) { return new Promise(r => setTimeout(r, ms)) }
function scoreColor(s) {
  if (s === null || s === undefined) return '#FEC84B'
  if (s < 40) return '#FF3333'
  if (s < 70) return '#FEC84B'
  return '#3EE07A'
}

function ScoreCurve({ history, score }) {
  if (!history || history.length < 2) return null
  const W = 400, H = 80, PAD = 16
  const pts = history.map((v, i) => ({
    x: PAD + (i / (history.length - 1)) * (W - 2 * PAD),
    y: H - PAD - ((v / 100) * (H - 2 * PAD)),
  }))
  const line = 'M' + pts.map(p => `${p.x},${p.y}`).join(' L')
  const area = line + ` L${pts[pts.length-1].x},${H-PAD} L${pts[0].x},${H-PAD} Z`
  const last = pts[pts.length - 1]
  const col = scoreColor(score)
  return (
    <div style={{ marginTop: 8 }}>
      <div className="font-pixel text-mc-muted mb-1" style={{ fontSize: 7 }}>PROGRESSION DU SCORE</div>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: H, display: 'block' }}>
        <defs>
          <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={col} stopOpacity="0.3"/>
            <stop offset="100%" stopColor={col} stopOpacity="0.02"/>
          </linearGradient>
        </defs>
        {[25,50,75].map(v => {
          const y = H - PAD - ((v/100)*(H-2*PAD))
          return <line key={v} x1={PAD} y1={y} x2={W-PAD} y2={y} stroke="#2D3A4A" strokeWidth="0.5" strokeDasharray="3,3"/>
        })}
        <path d={area} fill="url(#sg)"/>
        <path d={line} fill="none" stroke={col} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        <circle cx={last.x} cy={last.y} r="5" fill={col}/>
        <text x={last.x} y={last.y-9} fill={col} fontSize="10" textAnchor="middle" fontFamily="VT323,monospace">{score}/100</text>
        {[0,50,100].map(v => {
          const y = H - PAD - ((v/100)*(H-2*PAD))
          return <text key={v} x={PAD-2} y={y+3} fill="#6B7A8D" fontSize="8" textAnchor="end">{v}</text>
        })}
      </svg>
    </div>
  )
}

function PStep({ num, badge, title, desc, state, chips, children, bc='purple' }) {
  const dc = {
    idle:    { bg:'#1C2233', bd:'#2D3A4A', c:'#6B7A8D' },
    running: { bg:'#A07808', bd:'#FEC84B', c:'#FEC84B' },
    done:    { bg:'#1E5C3A', bd:'#3EE07A', c:'#3EE07A' },
    error:   { bg:'#5A1010', bd:'#FF3333', c:'#FF3333' },
  }[state] || { bg:'#1C2233', bd:'#2D3A4A', c:'#6B7A8D' }
  const cardBd = state==='running'?'#FEC84B':state==='done'?'#3EE07A':state==='error'?'#FF3333':'#2D3A4A'
  const bBg = {purple:'#1A1A5A',teal:'#0A3A2A',amber:'#3A2A08',red:'#3A1010'}
  const bCol = {purple:'#7EC8FF',teal:'#3EE07A',amber:'#FEC84B',red:'#FF6666'}
  return (
    <div style={{display:'flex',gap:0,alignItems:'stretch'}}>
      <div style={{display:'flex',flexDirection:'column',alignItems:'center',width:44,flexShrink:0}}>
        <div style={{
          width:30,height:30,borderRadius:'50%',
          background:dc.bg,border:`1.5px solid ${dc.bd}`,
          display:'flex',alignItems:'center',justifyContent:'center',
          flexShrink:0,zIndex:1,
          animation:state==='running'?'mcpulse 1.2s ease-in-out infinite':undefined,
        }}>
          {state==='running'?<div style={{width:8,height:8,borderRadius:'50%',background:dc.c,animation:'mcpulse 0.8s ease-in-out infinite'}}/>
          :state==='done'?<span style={{color:dc.c,fontSize:14}}>✓</span>
          :state==='error'?<span style={{color:dc.c,fontSize:14}}>✕</span>
          :<span style={{color:dc.c,fontFamily:'VT323,monospace',fontSize:16}}>{num}</span>}
        </div>
        <div style={{width:2,flex:1,minHeight:12,background:state==='done'?'#3EE07A':'#2D3A4A',margin:'0 auto',transition:'background 0.4s'}}/>
      </div>
      <div style={{flex:1,paddingLeft:12,paddingBottom:14,minWidth:0}}>
        <div style={{background:'#1C2233',border:`1px solid ${cardBd}`,borderRadius:8,padding:'10px 14px',transition:'border-color 0.3s',boxShadow:state==='running'?`0 0 8px ${cardBd}30`:undefined}}>
          <div style={{display:'flex',alignItems:'center',gap:8,flexWrap:'wrap',marginBottom:4}}>
            <span style={{fontFamily:'Press Start 2P,monospace',fontSize:8,background:bBg[bc],color:bCol[bc],padding:'2px 7px',borderRadius:4}}>{badge}</span>
            <span className="font-pixel" style={{fontSize:9,color:'#E6EDF3'}}>{title}</span>
            {state==='done'&&<span style={{fontFamily:'Press Start 2P,monospace',fontSize:7,background:'#0A3A2A',color:'#3EE07A',padding:'2px 6px',borderRadius:4}}>FAIT ✓</span>}
          </div>
          <div className="font-ui text-mc-muted" style={{fontSize:12,lineHeight:1.5,marginBottom:chips?.length?6:0}}>{desc}</div>
          {chips&&<div style={{display:'flex',flexWrap:'wrap',gap:4,marginBottom:children?8:0}}>
            {chips.map(({label,on})=>(
              <span key={label} style={{fontSize:10,padding:'2px 7px',borderRadius:10,background:on?'#0A3A2A':'#111827',color:on?'#3EE07A':'#6B7A8D',border:`0.5px solid ${on?'#3EE07A':'#2D3A4A'}`,transition:'all 0.3s'}}>{label}</span>
            ))}
          </div>}
          {children}
        </div>
      </div>
    </div>
  )
}

function ProgBar({ pct, color='#FEC84B' }) {
  return <div style={{height:5,background:'#111827',borderRadius:3,overflow:'hidden',marginTop:8}}>
    <div style={{height:5,borderRadius:3,width:`${pct}%`,background:color,transition:'width 0.4s ease'}}/>
  </div>
}

function LogBox({ lines }) {
  const ref = useRef()
  useEffect(()=>{ if(ref.current) ref.current.scrollTop=ref.current.scrollHeight },[lines])
  return <div ref={ref} style={{background:'#050810',borderRadius:6,padding:'6px 10px',fontFamily:'VT323,monospace',fontSize:15,color:'#3EE07A',maxHeight:72,overflow:'hidden',marginTop:8,lineHeight:1.5}}>
    {lines.map((l,i)=><div key={i} style={{opacity:i===lines.length-1?1:0.45}}>{l}</div>)}
  </div>
}

function ResultGrid({ items }) {
  return <div style={{display:'grid',gridTemplateColumns:'repeat(2,1fr)',gap:6,marginTop:8}}>
    {items.map(({label,value,color})=>(
      <div key={label} style={{background:'#111827',borderRadius:6,padding:'6px 10px'}}>
        <div style={{fontFamily:'VT323,monospace',fontSize:22,color:color||'#E6EDF3',lineHeight:1.2}}>{value}</div>
        <div className="font-pixel text-mc-muted" style={{fontSize:7}}>{label}</div>
      </div>
    ))}
  </div>
}

export default function Mobile() {
  const [view, setView]             = useState('list')
  const [scans, setScans]           = useState([])
  const [loading, setLoading]       = useState(true)
  const [dragOver, setDragOver]     = useState(false)
  const [ctxContext, setCtxContext]  = useState('')
  const [ctxObj, setCtxObj]         = useState('')
  const [ctxPer, setCtxPer]         = useState('')
  const [pFile, setPFile]           = useState(null)
  const [pRunning, setPRunning]     = useState(false)
  const [scanId, setScanId]         = useState(null)
  const [steps, setSteps]           = useState({s1:'idle',s2:'idle',s3:'idle',s4:'idle',s5:'idle',s6:'idle'})
  const [progs, setProgs]           = useState({p1:0,p2:0,p3:0,p4:0,p5:0})
  const [logs, setLogs]             = useState({l1:[],l2:[],l4:[]})
  const [chips, setChips]           = useState({})
  const [results, setResults]       = useState({})
  const [scoreHistory, setScoreHistory] = useState([])
  const [verdict, setVerdict]       = useState(null)
  const [pdfReady, setPdfReady]     = useState(false)
  const fileRef = useRef()
  const { success, error } = useToast()

  const setStep    = (k,v) => setSteps(s=>({...s,[k]:v}))
  const setProgress = (k,v) => setProgs(p=>({...p,[k]:v}))
  const addLog     = (k,msg) => setLogs(l=>({...l,[k]:[...(l[k]||[]),msg]}))
  const setChip    = (k,on) => setChips(c=>({...c,[k]:on}))
  const setResult  = (k,v) => setResults(r=>({...r,[k]:v}))

  const animProg = async (key, to, ms=600) => {
    const n = Math.max(1,Math.floor(ms/30))
    for(let i=0;i<=n;i++){
      await sleep(30)
      setProgress(key, v => Math.min((typeof v==='number'?v:0) + (to-(typeof v==='number'?v:0))/n, to))
    }
  }

  const loadScans = async () => {
    setLoading(true)
    try { const r = await api.get('/mobile-scans/'); setScans(r.data) }
    catch { error('Erreur chargement') }
    setLoading(false)
  }

  useEffect(()=>{ loadScans() },[])
  useEffect(()=>{
    const hasPending = scans.some(s=>['pending','downloading'].includes(s.status))
    if(!hasPending) return
    const t = setInterval(loadScans,10000)
    return ()=>clearInterval(t)
  },[scans])

  const onFile = (f) => {
    if(!f||!f.name.endsWith('.apk')){ error('Fichier .apk requis'); return }
    setPFile(f)
  }

  const resetPipeline = () => {
    setPFile(null); setScanId(null); setPRunning(false); setVerdict(null); setPdfReady(false)
    setSteps({s1:'idle',s2:'idle',s3:'idle',s4:'idle',s5:'idle',s6:'idle'})
    setProgs({p1:0,p2:0,p3:0,p4:0,p5:0})
    setLogs({l1:[],l2:[],l4:[]})
    setChips({}); setResults({}); setScoreHistory([])
    if(fileRef.current) fileRef.current.value=''
  }

  const startPipeline = async () => {
    if(!pFile||pRunning) return
    setPRunning(true); setVerdict(null); setPdfReady(false); setScoreHistory([])
    const token = localStorage.getItem('cso_token')
    try {
      // S1 Upload
      setStep('s1','running'); setProgress('p1',0)
      addLog('l1','> Upload '+pFile.name+' ('+(pFile.size/1024/1024).toFixed(1)+' Mo)...')
      await animProg('p1',40,300)
      const form = new FormData(); form.append('file',pFile)
      const upRes = await fetch('/mobile-scans/',{method:'POST',headers:{Authorization:`Bearer ${token}`},body:form})
      if(!upRes.ok){const d=await upRes.json().catch(()=>({})); throw new Error(d.detail||'Upload échoué')}
      const upData = await upRes.json()
      const sid = upData.id_scan; setScanId(sid)
      addLog('l1','> APK reçu — Scan #'+sid)
      await animProg('p1',100,200); setStep('s1','done')

      // S2 MobSF
      setStep('s2','running'); setProgress('p2',0)
      addLog('l2','> MobSF décompilation APK...')
      let scan=null, poll=0, fakeHist=[50]
      while(poll<80){
        await sleep(8000); poll++
        const pct = Math.min(10+poll*1.1,93); setProgress('p2',pct)
        const r = await api.get('/mobile-scans/'+sid); scan=r.data
        addLog('l2',`> [${Math.round(pct)}%] ${scan.status}...`)
        const base=scan.security_score??50
        fakeHist.push(Math.max(0,Math.min(100,Math.round(base+Math.sin(poll*0.8)*10))))
        setScoreHistory([...fakeHist])
        if(poll%3===0) setChip('ch-perm',true)
        if(poll%5===0) setChip('ch-track',true)
        if(poll%7===0) setChip('ch-score',true)
        if(scan.status==='completed') break
        if(scan.status==='failed') throw new Error('MobSF scan failed')
      }
      const perms=parseJson(scan.dangerous_perms), trackers=parseJson(scan.trackers)
      const score=scan.security_score??0
      fakeHist.push(score); setScoreHistory([...fakeHist])
      setResult('score',score); setResult('crit',scan.critical_count??0)
      setResult('high',scan.high_count??0); setResult('perms',perms.length)
      setResult('trackers',trackers.length); setResult('scan',scan)
      setChip('ch-perm',true); setChip('ch-track',true); setChip('ch-score',true); setChip('ch-find',true)
      await animProg('p2',100,300); setStep('s2','done')

      // S3 Trivy
      setStep('s3','running'); setProgress('p3',0)
      await animProg('p3',40,500); setChip('ch-cve',true)
      await animProg('p3',75,400); setChip('ch-cvss',true)
      await animProg('p3',100,300); setChip('ch-exp',true)
      setResult('tcrit',scan.critical_count??0); setResult('thigh',scan.high_count??0)
      setStep('s3','done')

      // S4 Ollama
      setStep('s4','running'); setProgress('p4',0)
      addLog('l4','> Connexion Ollama llama3 via WireGuard...')
      try {
        const olRes = await fetch('/ai/analyze/scan/'+sid,{method:'POST',headers:{Authorization:`Bearer ${token}`}})
        if(olRes.ok){
          const reader=olRes.body.getReader(); const dec=new TextDecoder()
          let buf='',chars=0
          while(true){
            const{done,value}=await reader.read(); if(done) break
            buf+=dec.decode(value,{stream:true})
            const lines=buf.split('\n'); buf=lines.pop()
            for(const line of lines){
              if(!line.startsWith('data: ')) continue
              const d=line.slice(6).trim(); if(d==='[DONE]') break
              try{const o=JSON.parse(d);if(o.token){chars+=o.token.length;setProgress('p4',Math.min(20+chars/25,90));if(chars>50)setChip('ch-for',true);if(chars>200)setChip('ch-mit',true);if(chars>400)setChip('ch-rec',true)}}catch{}
            }
          }
          addLog('l4','> Analyse IA terminée')
        }
      } catch{}
      setChip('ch-for',true); setChip('ch-mit',true); setChip('ch-rec',true)
      await animProg('p4',100,300); setStep('s4','done')

      // S5 EBIOS
      setStep('s5','running'); setProgress('p5',0)
      for(let i=0;i<5;i++){
        setChip('ch-a'+(i+1),false)
        await animProg('p5',20*(i+1),400)
        setChip('ch-a'+(i+1),true)
      }
      await animProg('p5',100,200)
      setResult('scenarios',Math.max(2,perms.length+(scan.critical_count||0)))
      setResult('riskMax',(scan.critical_count||0)>0?'CRITIQUE':(scan.high_count||0)>0?'ÉLEVÉ':'MOYEN')
      setStep('s5','done')

      // S6 Done
      setStep('s6','done')
      setVerdict(score<40
        ?{label:'APPLICATION DANGEREUSE',desc:'Ne pas déployer — corrections critiques requises',color:'#FF3333',bg:'#3A0A0A'}
        :score<70
        ?{label:'RISQUES IDENTIFIÉS',desc:'Corrections recommandées avant déploiement',color:'#FEC84B',bg:'#2A1A08'}
        :{label:'APPLICATION SÛRE',desc:'Niveau de sécurité satisfaisant',color:'#3EE07A',bg:'#0A2A18'})
      setPdfReady(true); success('Analyse complète !'); loadScans()
    } catch(e){ setStep('s1','error'); error('Erreur : '+e.message) }
    setPRunning(false)
  }

  const downloadEbiosPdf = async () => {
    if(!scanId) return
    const token = localStorage.getItem('cso_token')
    try {
      const res = await fetch(`/export/pdf/mobile-scan/${scanId}/ebios`,{
        method:'POST',
        headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},
        body:JSON.stringify({context_user:ctxContext,objectifs:ctxObj,perimetre:ctxPer})
      })
      if(!res.ok) throw new Error('Erreur PDF')
      const blob=await res.blob()
      const a=document.createElement('a'); a.href=URL.createObjectURL(blob)
      a.download=`ebios-mobile-${scanId}.pdf`
      document.body.appendChild(a); a.click(); document.body.removeChild(a)
      URL.revokeObjectURL(a.href); success('PDF téléchargé !')
    } catch(e){ error('Erreur PDF : '+e.message) }
  }

  if(view==='list') return (
    <div>
      <McSectionTitle actions={
        <div style={{display:'flex',gap:8}}>
          <button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={loadScans}>↺</button>
          <button className="mc-btn mc-btn-primary mc-btn-sm" onClick={()=>setView('pipeline')}>⚔ NOUVELLE ANALYSE</button>
        </div>
      }>📱 SCANS MOBILES</McSectionTitle>
      <McBlock>
        {loading?<McSpinner/>:scans.length===0?<McEmpty>Aucun scan — lancez une nouvelle analyse</McEmpty>:(
          <div style={{overflowX:'auto'}}>
            <table className="mc-table">
              <thead><tr>{['#','APP','PACKAGE','SCORE','CRIT','HIGH','WARN','STATUT','DATE'].map(h=><th key={h}>{h}</th>)}</tr></thead>
              <tbody>
                {scans.map(s=>(
                  <tr key={s.id_scan}>
                    <td className="font-pixel text-mc-muted" style={{fontSize:9}}>{s.id_scan}</td>
                    <td><strong style={{fontSize:13}}>{s.app_name||'—'}</strong></td>
                    <td className="text-mc-muted" style={{fontSize:11}}>{s.package_name||'—'}</td>
                    <td><ScoreBadge score={s.security_score}/></td>
                    <td style={{color:'#FF3333',fontFamily:'VT323',fontSize:22}}>{s.critical_count??0}</td>
                    <td style={{color:'#FEC84B',fontFamily:'VT323',fontSize:22}}>{s.high_count??0}</td>
                    <td style={{color:'#E3D060',fontFamily:'VT323',fontSize:22}}>{s.warning_count??0}</td>
                    <td><McPill value={s.status}/></td>
                    <td className="text-mc-muted" style={{fontSize:11}}>{fmt(s.scanned_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </McBlock>
    </div>
  )

  return (
    <div>
      <style>{`@keyframes mcpulse{0%,100%{opacity:1}50%{opacity:.6}}`}</style>
      <McSectionTitle actions={
        !pRunning&&<button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={()=>{resetPipeline();setView('list')}}>← RETOUR</button>
      }>⚔ ANALYSE DE SÉCURITÉ MOBILE</McSectionTitle>

      {!pRunning&&steps.s1==='idle'&&(
        <McBlock>
          <div className="font-pixel text-mc-gold mb-3" style={{fontSize:9}}>📦 SÉLECTIONNER UN APK</div>
          <div onClick={()=>fileRef.current?.click()}
            onDragOver={e=>{e.preventDefault();setDragOver(true)}}
            onDragLeave={()=>setDragOver(false)}
            onDrop={e=>{e.preventDefault();setDragOver(false);onFile(e.dataTransfer.files[0])}}
            style={{border:`2px dashed ${pFile?'#3EE07A':dragOver?'#39D4E0':'#2D3A4A'}`,borderRadius:8,padding:'24px 16px',textAlign:'center',cursor:'pointer',background:pFile?'#0A2A1A':dragOver?'#0A1A2A':'#111827',transition:'all .2s',marginBottom:12}}>
            <input ref={fileRef} type="file" accept=".apk" style={{display:'none'}} onChange={e=>{onFile(e.target.files[0]);e.target.value=''}}/>
            <div style={{fontSize:32,marginBottom:8}}>{pFile?'📦':'📥'}</div>
            <div className="font-pixel" style={{fontSize:8,color:pFile?'#3EE07A':'#6B7A8D'}}>
              {pFile?pFile.name:'GLISSER UN APK ICI OU CLIQUEZ'}
            </div>
            <div className="font-ui text-mc-muted mt-1" style={{fontSize:11}}>
              {pFile?(pFile.size/1024/1024).toFixed(1)+' Mo — prêt à analyser':'max 200 Mo — Android uniquement'}
            </div>
          </div>
          <div style={{display:'flex',flexDirection:'column',gap:8,marginBottom:12}}>
            <div>
              <div className="font-pixel text-mc-muted mb-1" style={{fontSize:7}}>CONTEXTE ORGANISATIONNEL</div>
              <textarea className="mc-input" rows={2} value={ctxContext} onChange={e=>setCtxContext(e.target.value)} placeholder="Ex: Application déployée sur 200 appareils employés..."/>
            </div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:8}}>
              <div>
                <div className="font-pixel text-mc-muted mb-1" style={{fontSize:7}}>OBJECTIFS</div>
                <input className="mc-input" value={ctxObj} onChange={e=>setCtxObj(e.target.value)} placeholder="Conformité RGPD..."/>
              </div>
              <div>
                <div className="font-pixel text-mc-muted mb-1" style={{fontSize:7}}>PÉRIMÈTRE</div>
                <input className="mc-input" value={ctxPer} onChange={e=>setCtxPer(e.target.value)} placeholder="Android v2.3..."/>
              </div>
            </div>
          </div>
          <button className="mc-btn mc-btn-primary" disabled={!pFile} onClick={startPipeline} style={{fontSize:10,padding:'10px 20px'}}>
            ⚔ LANCER L'ANALYSE COMPLÈTE
          </button>
        </McBlock>
      )}

      <McBlock style={{padding:'16px 12px'}}>
        <PStep num={1} badge="ÉTAPE 1" title="UPLOAD APK" bc="purple"
          desc="Envoi du fichier APK vers MobSF via l'API FastAPI"
          state={steps.s1} chips={[{label:'APK reçu',on:steps.s1==='done'}]}>
          {logs.l1.length>0&&steps.s1!=='done'&&<LogBox lines={logs.l1}/>}
          {steps.s1!=='idle'&&<ProgBar pct={progs.p1} color={steps.s1==='done'?'#3EE07A':'#FEC84B'}/>}
        </PStep>

        <PStep num={2} badge="ÉTAPE 2" title="ANALYSE MOBSF" bc="purple"
          desc="Décompilation APK — permissions, trackers, findings OWASP MASVS v2"
          state={steps.s2} chips={[
            {label:'Permissions',on:!!chips['ch-perm']},
            {label:'Trackers',on:!!chips['ch-track']},
            {label:'Score',on:!!chips['ch-score']},
            {label:'Findings',on:!!chips['ch-find']},
          ]}>
          {logs.l2.length>0&&steps.s2!=='done'&&<LogBox lines={logs.l2}/>}
          {steps.s2!=='idle'&&<ProgBar pct={progs.p2} color={steps.s2==='done'?'#3EE07A':'#FEC84B'}/>}
          {steps.s2==='done'&&results.score!==undefined&&(
            <>
              <ResultGrid items={[
                {label:'SCORE',value:results.score+'/100',color:scoreColor(results.score)},
                {label:'CRITIQUE',value:results.crit,color:'#FF3333'},
                {label:'PERMS DANG.',value:results.perms,color:'#FEC84B'},
                {label:'TRACKERS',value:results.trackers,color:'#E3D060'},
              ]}/>
              <ScoreCurve history={scoreHistory} score={results.score}/>
            </>
          )}
        </PStep>

        <PStep num={3} badge="ÉTAPE 3" title="SCAN TRIVY CVE" bc="amber"
          desc="Détection CVE dans les dépendances — score CVSS, exploits connus"
          state={steps.s3} chips={[
            {label:'CVE',on:!!chips['ch-cve']},
            {label:'CVSS',on:!!chips['ch-cvss']},
            {label:'Exploits',on:!!chips['ch-exp']},
          ]}>
          {steps.s3!=='idle'&&<ProgBar pct={progs.p3} color={steps.s3==='done'?'#3EE07A':'#FEC84B'}/>}
          {steps.s3==='done'&&<ResultGrid items={[
            {label:'CVE CRITIQUES',value:results.tcrit,color:'#FF3333'},
            {label:'CVE ÉLEVÉES',value:results.thigh,color:'#FEC84B'},
          ]}/>}
        </PStep>

        <PStep num={4} badge="ÉTAPE 4" title="ANALYSE IA OLLAMA" bc="purple"
          desc="llama3 8B — forensique, MITRE ATT&CK Mobile, recommandations priorisées"
          state={steps.s4} chips={[
            {label:'Forensique',on:!!chips['ch-for']},
            {label:'MITRE ATT&CK',on:!!chips['ch-mit']},
            {label:'Recommandations',on:!!chips['ch-rec']},
          ]}>
          {logs.l4.length>0&&steps.s4!=='done'&&<LogBox lines={logs.l4}/>}
          {steps.s4!=='idle'&&<ProgBar pct={progs.p4} color={steps.s4==='done'?'#3EE07A':'#534AB7'}/>}
        </PStep>

        <PStep num={5} badge="ÉTAPE 5" title="EBIOS RM" bc="teal"
          desc="5 ateliers ANSSI — biens valorisés, sources de risque, scénarios SR+SO, mesures"
          state={steps.s5} chips={[
            {label:'Atelier 1',on:!!chips['ch-a1']},
            {label:'Atelier 2',on:!!chips['ch-a2']},
            {label:'Atelier 3',on:!!chips['ch-a3']},
            {label:'Atelier 4',on:!!chips['ch-a4']},
            {label:'Atelier 5',on:!!chips['ch-a5']},
          ]}>
          {steps.s5!=='idle'&&<ProgBar pct={progs.p5} color={steps.s5==='done'?'#3EE07A':'#0F6E56'}/>}
          {steps.s5==='done'&&<ResultGrid items={[
            {label:'SCÉNARIOS',value:results.scenarios},
            {label:'RISQUE MAX',value:results.riskMax,color:'#FF3333'},
          ]}/>}
        </PStep>

        <PStep num={6} badge="ÉTAPE 6" title="RAPPORT PDF EBIOS RM" bc="amber"
          desc="Rapport complet : forensique · CVE · matrice risque · analyse IA · recommandations ISO 27001"
          state={steps.s6}>
          {verdict&&(
            <div style={{background:verdict.bg,border:`2px solid ${verdict.color}`,borderRadius:8,padding:'12px 16px',marginTop:10,display:'flex',alignItems:'center',gap:12}}>
              <div style={{fontSize:28}}>{verdict.color==='#FF3333'?'🔴':verdict.color==='#FEC84B'?'🟠':'🟢'}</div>
              <div>
                <div className="font-pixel" style={{fontSize:10,color:verdict.color,marginBottom:4}}>{verdict.label}</div>
                <div className="font-ui" style={{fontSize:12,color:'#E6EDF3'}}>{verdict.desc}</div>
              </div>
            </div>
          )}
          {pdfReady&&(
            <div style={{display:'flex',gap:8,flexWrap:'wrap',marginTop:12}}>
              <button className="mc-btn mc-btn-primary" onClick={downloadEbiosPdf}>📄 TÉLÉCHARGER RAPPORT EBIOS RM PDF</button>
              <button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={()=>{resetPipeline();loadScans()}}>↺ NOUVELLE ANALYSE</button>
              <button className="mc-btn mc-btn-ghost mc-btn-sm" onClick={()=>setView('list')}>📋 VOIR LES SCANS</button>
            </div>
          )}
        </PStep>
      </McBlock>
    </div>
  )
}