import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import MinecraftWorld from '../components/MinecraftWorld'
import api from '../services/api'

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [frame, setFrame] = useState(0)

  useEffect(() => {
    if (localStorage.getItem('cso_token')) navigate('/dashboard')
    const t = setInterval(() => setFrame(f => (f + 1) % 4), 500)
    return () => clearInterval(t)
  }, [])

  const playerFrames = ['🧍', '🚶', '🧍', '🏃']

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.post('/auth/login', { email, password })
      localStorage.setItem('cso_token', res.data.access_token)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Identifiants incorrects')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center relative">
      <MinecraftWorld />

      <div className="relative z-10 w-full max-w-md px-4">
        {/* Title card */}
        <div className="text-center mb-8">
          {/* Pixel shield big */}
          <div className="flex justify-center mb-4">
            <div style={{
              width: 64, height: 64,
              background: '#39D4E0',
              imageRendering: 'pixelated',
              boxShadow: 'inset -8px -10px 0 rgba(0,0,0,0.4), inset 6px 6px 0 rgba(255,255,255,0.2), 0 0 40px rgba(57,212,224,0.5)',
              clipPath: 'polygon(50% 0%, 100% 25%, 100% 60%, 50% 100%, 0% 60%, 0% 25%)',
            }} />
          </div>
          <h1
            className="font-pixel text-mc-diamond"
            style={{ fontSize: 14, letterSpacing: 3, textShadow: '0 0 20px rgba(57,212,224,0.8), 3px 3px 0 rgba(0,0,0,0.8)' }}
          >
            CLOUDSECOPS
          </h1>
          <p className="font-pixel text-mc-muted mt-2" style={{ fontSize: 8, letterSpacing: 1 }}>
            CONNEXION AU SERVEUR
          </p>
        </div>

        {/* Login block */}
        <div className="mc-block p-6">
          {/* Pixel decorative header */}
          <div className="flex items-center gap-2 mb-5 pb-3" style={{ borderBottom: '2px solid #2D3A4A' }}>
            <div style={{ width: 16, height: 16, background: '#1A4BE6', boxShadow: 'inset -2px -3px 0 rgba(0,0,0,0.5)' }} />
            <span className="font-pixel text-mc-light" style={{ fontSize: 9 }}>
              AUTHENTIFICATION
            </span>
            <span style={{ fontSize: 18 }}>{playerFrames[frame]}</span>
          </div>

          {error && (
            <div
              className="font-pixel mb-4 p-3"
              style={{
                fontSize: 8,
                background: '#3D1010',
                border: '2px solid #FF3333',
                color: '#FF6666',
                boxShadow: 'inset -2px -3px 0 rgba(0,0,0,0.4)',
              }}
            >
              ❌ {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block font-pixel text-mc-muted mb-2" style={{ fontSize: 8 }}>
                ✉ ADRESSE E-MAIL
              </label>
              <input
                className="mc-input"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="admin@cloudsecops.dev"
                required
                autoComplete="username"
              />
            </div>

            <div className="mb-6">
              <label className="block font-pixel text-mc-muted mb-2" style={{ fontSize: 8 }}>
                🔑 MOT DE PASSE
              </label>
              <input
                className="mc-input"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="mc-btn mc-btn-primary w-full"
              style={{ fontSize: 10, padding: '12px 0' }}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="mc-spinner" style={{ width: 12, height: 12 }} />
                  CONNEXION...
                </span>
              ) : (
                '▶ SE CONNECTER'
              )}
            </button>
          </form>

          {/* Deco bottom */}
          <div className="flex items-center justify-center gap-3 mt-4 pt-3" style={{ borderTop: '2px solid #2D3A4A' }}>
            {['🌿', '💎', '⚔️', '🛡️'].map((icon, i) => (
              <span key={i} style={{ fontSize: 16, opacity: 0.6 }}>{icon}</span>
            ))}
          </div>
        </div>

        {/* API link */}
        <div className="text-center mt-3">
          <a
            href="/docs"
            target="_blank"
            className="font-pixel text-mc-muted hover:text-mc-diamond"
            style={{ fontSize: 8, textDecoration: 'none', letterSpacing: 0.5 }}
          >
            📖 DOCUMENTATION API (SWAGGER)
          </a>
        </div>
      </div>
    </div>
  )
}
