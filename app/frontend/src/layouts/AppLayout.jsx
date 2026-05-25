import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import MinecraftWorld from '../components/MinecraftWorld'
import { ToastProvider } from '../components/McToast'
import api from '../services/api'

const TABS = [
  { id: 'profile',   label: '👤 PROFIL',      adminOnly: false },
  { id: 'users',     label: '👥 JOUEURS',      adminOnly: true  },
  { id: 'scans',     label: '🔍 SCANS TRIVY',  adminOnly: true  },
  { id: 'incidents', label: '⚠️ INCIDENTS',    adminOnly: true  },
  { id: 'reports',   label: '📜 RAPPORTS',     adminOnly: true  },
  { id: 'mobile',    label: '📱 MOBILE',       adminOnly: true  },
  { id: 'ebios',     label: '🛡️ EBIOS RM',    adminOnly: true  },
  { id: 'ai',        label: '🤖 IA OLLAMA',    adminOnly: true  },
  { id: 'logs',      label: '📡 LOGS AWS',     adminOnly: true  },
]

export default function AppLayout({ children, activeTab, onTabChange }) {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('cso_token')
    if (!token) { navigate('/login'); return }
    api.get('/users/me')
      .then(r => { setUser(r.data); setLoading(false) })
      .catch(() => { navigate('/login') })
  }, [])

  const logout = () => {
    localStorage.removeItem('cso_token')
    navigate('/login')
  }

  const visibleTabs = TABS.filter(t => !t.adminOnly || user?.role === 'admin')

  return (
    <div className="min-h-screen flex flex-col" style={{ position: 'relative' }}>
      <MinecraftWorld />

      {/* Nav */}
      <nav
        className="sticky top-0 z-20 flex items-center justify-between px-5"
        style={{
          background: 'rgba(10,14,26,0.95)',
          borderBottom: '3px solid #2D3A4A',
          backdropFilter: 'blur(4px)',
          height: 52,
          boxShadow: 'inset 0 -3px 0 rgba(57,212,224,0.15)',
        }}
      >
        {/* Brand */}
        <div className="flex items-center gap-3">
          {/* Pixel shield */}
          <div style={{
            width: 24, height: 24,
            background: '#39D4E0',
            imageRendering: 'pixelated',
            boxShadow: 'inset -3px -4px 0 rgba(0,0,0,0.4)',
            clipPath: 'polygon(50% 0%, 100% 25%, 100% 60%, 50% 100%, 0% 60%, 0% 25%)',
          }} />
          <span className="font-pixel text-mc-diamond" style={{ fontSize: 11, letterSpacing: 2, textShadow: '0 0 10px rgba(57,212,224,0.6)' }}>
            CloudSecOps
          </span>
          {/* Torch */}
          <div style={{
            width: 6, height: 6, background: '#FEC84B',
            animation: 'torch 0.15s steps(2) infinite',
          }} />
        </div>

        {/* Right */}
        <div className="flex items-center gap-3">
          {loading ? (
            <div className="mc-spinner" />
          ) : (
            <>
              <div
                className="font-pixel hidden sm:block"
                style={{
                  fontSize: 8,
                  background: '#1C2233',
                  border: '2px solid #2D3A4A',
                  padding: '4px 10px',
                  boxShadow: 'inset -2px -3px 0 rgba(0,0,0,0.4)',
                  color: '#39D4E0',
                }}
              >
                {user?.email}
                {' '}
                <span className={`mc-pill mc-pill-${user?.role}`}>{user?.role}</span>
              </div>
              <a
                href="/docs"
                target="_blank"
                className="mc-btn mc-btn-accent mc-btn-sm"
                style={{ textDecoration: 'none' }}
              >API</a>
              <button className="mc-btn mc-btn-danger mc-btn-sm" onClick={logout}>
                QUITTER
              </button>
            </>
          )}
        </div>
      </nav>

      {/* Tabs */}
      <div
        className="sticky top-[52px] z-20 flex overflow-x-auto"
        style={{
          background: 'rgba(10,14,26,0.95)',
          borderBottom: '2px solid #2D3A4A',
          backdropFilter: 'blur(4px)',
          scrollbarWidth: 'none',
          gap: 0,
          paddingLeft: 20,
        }}
      >
        {visibleTabs.map(tab => (
          <button
            key={tab.id}
            className={`mc-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Main content */}
      <main
        className="flex-1 relative z-10"
        style={{
          maxWidth: 1100,
          margin: '0 auto',
          padding: '24px 20px 80px',
          width: '100%',
        }}
      >
        {children}
      </main>

      <ToastProvider />

      {/* Bottom pixel bar */}
      <div className="fixed bottom-0 left-0 right-0 pointer-events-none" style={{ zIndex: 5 }}>
        <div style={{ height: 4, background: '#39D4E0', opacity: 0.3 }} />
      </div>
    </div>
  )
}
