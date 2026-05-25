import { useEffect, useState } from 'react'
import McBlock, { McSectionTitle, McStat, McSpinner } from '../../components/McBlock'
import { RolePill, StatusPill } from '../../components/McPill'
import api from '../../services/api'

function fmt(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })
}

export default function Profile() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/users/me').then(r => { setUser(r.data); setLoading(false) })
  }, [])

  if (loading) return <McSpinner />

  return (
    <div>
      <McSectionTitle>👤 MON PROFIL</McSectionTitle>

      {/* Inventory-style profile card */}
      <McBlock>
        <div className="flex items-start gap-6 flex-wrap">
          {/* Avatar pixel */}
          <div style={{
            width: 80, height: 80,
            background: '#1A4BE6',
            imageRendering: 'pixelated',
            boxShadow: 'inset -8px -10px 0 rgba(0,0,0,0.4), inset 6px 6px 0 rgba(255,255,255,0.1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 36,
            flexShrink: 0,
          }}>
            {user?.role === 'admin' ? '🧙' : '🧑'}
          </div>

          <div className="flex-1 min-w-0">
            <div className="font-pixel text-mc-light mb-1" style={{ fontSize: 13, letterSpacing: 1 }}>
              {user?.email}
            </div>
            <div className="flex gap-2 items-center mb-3">
              <RolePill role={user?.role} />
              <StatusPill active={user?.is_active} />
            </div>

            <div className="grid grid-cols-2 gap-3" style={{ maxWidth: 400 }}>
              {[
                { label: 'ID JOUEUR', val: `#${user?.id_user}` },
                { label: 'MEMBRE DEPUIS', val: fmt(user?.created_at) },
              ].map(({ label, val }) => (
                <div key={label} style={{ background: '#0A0E1A', border: '2px solid #2D3A4A', padding: '8px 12px' }}>
                  <div className="font-pixel text-mc-muted" style={{ fontSize: 7, marginBottom: 4 }}>{label}</div>
                  <div className="font-ui text-mc-light" style={{ fontSize: 13 }}>{val}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </McBlock>

      {/* Achievements */}
      <McBlock>
        <div className="font-pixel text-mc-gold mb-4" style={{ fontSize: 9 }}>🏆 SUCCÈS DÉBLOQUÉS</div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { icon: '🔐', label: 'CONNECTÉ', desc: 'Première connexion' },
            { icon: '🛡️', label: 'OPÉRATEUR', desc: 'Accès dashboard' },
            { icon: '⚔️', label: 'ANALYSTE', desc: user?.role === 'admin' ? 'Rôle admin' : 'Rôle user' },
            { icon: '💎', label: 'CRAFTED', desc: 'CloudSecOps actif' },
          ].map(a => (
            <div
              key={a.label}
              style={{
                background: '#111827',
                border: '2px solid #2D3A4A',
                padding: '12px',
                textAlign: 'center',
                boxShadow: 'inset -2px -3px 0 rgba(0,0,0,0.4)',
              }}
            >
              <div style={{ fontSize: 28 }}>{a.icon}</div>
              <div className="font-pixel text-mc-gold mt-2" style={{ fontSize: 7 }}>{a.label}</div>
              <div className="font-ui text-mc-muted mt-1" style={{ fontSize: 11 }}>{a.desc}</div>
            </div>
          ))}
        </div>
      </McBlock>
    </div>
  )
}
