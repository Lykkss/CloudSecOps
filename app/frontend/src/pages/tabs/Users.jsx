import { useEffect, useState } from 'react'
import McBlock, { McSectionTitle, McSpinner, McEmpty } from '../../components/McBlock'
import { RolePill, StatusPill } from '../../components/McPill'
import { useToast } from '../../components/McToast'
import api from '../../services/api'

function fmt(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })
}

export default function Users() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [me, setMe] = useState(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('2')
  const { success, error } = useToast()

  const load = async () => {
    setLoading(true)
    const [usersRes, meRes] = await Promise.all([api.get('/users/'), api.get('/users/me')])
    setUsers(usersRes.data)
    setMe(meRes.data)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const createUser = async (e) => {
    e.preventDefault()
    try {
      await api.post('/users/', { email, password, role_id: parseInt(role) })
      success('Joueur créé !')
      setEmail(''); setPassword('')
      load()
    } catch (err) {
      error(err.response?.data?.detail || 'Erreur création')
    }
  }

  const deleteUser = async (id) => {
    if (!confirm('Désactiver ce joueur ?')) return
    try {
      await api.delete(`/users/${id}`)
      success('Joueur désactivé')
      load()
    } catch (err) {
      error(err.response?.data?.detail || 'Erreur')
    }
  }

  return (
    <div>
      <McSectionTitle>👥 GESTION DES JOUEURS</McSectionTitle>

      {/* Create form */}
      <McBlock>
        <div className="font-pixel text-mc-emerald mb-4" style={{ fontSize: 9 }}>➕ NOUVEAU JOUEUR</div>
        <form onSubmit={createUser} className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block font-pixel text-mc-muted mb-1" style={{ fontSize: 7 }}>E-MAIL</label>
            <input className="mc-input" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="user@example.com" required style={{ width: 220 }} />
          </div>
          <div>
            <label className="block font-pixel text-mc-muted mb-1" style={{ fontSize: 7 }}>MOT DE PASSE</label>
            <input className="mc-input" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="min 8 chars" required minLength={8} style={{ width: 160 }} />
          </div>
          <div>
            <label className="block font-pixel text-mc-muted mb-1" style={{ fontSize: 7 }}>RÔLE</label>
            <select className="mc-select" value={role} onChange={e => setRole(e.target.value)} style={{ width: 120 }}>
              <option value="2">user</option>
              <option value="1">admin</option>
            </select>
          </div>
          <button type="submit" className="mc-btn mc-btn-primary">CRÉER</button>
        </form>
      </McBlock>

      {/* Users table */}
      <McBlock>
        {loading ? <McSpinner /> : users.length === 0 ? <McEmpty>Aucun joueur</McEmpty> : (
          <div className="overflow-x-auto">
            <table className="mc-table">
              <thead>
                <tr>
                  {['#', 'E-MAIL', 'RÔLE', 'STATUT', 'CRÉÉ LE', 'ACTION'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id_user}>
                    <td className="font-pixel text-mc-muted" style={{ fontSize: 9 }}>{u.id_user}</td>
                    <td className="font-ui" style={{ fontSize: 13 }}>{u.email}</td>
                    <td><RolePill role={u.role} /></td>
                    <td><StatusPill active={u.is_active} /></td>
                    <td className="text-mc-muted" style={{ fontSize: 12 }}>{fmt(u.created_at)}</td>
                    <td>
                      {u.id_user !== me?.id_user && u.is_active && (
                        <button className="mc-btn mc-btn-danger mc-btn-sm" onClick={() => deleteUser(u.id_user)}>
                          BAN
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </McBlock>
    </div>
  )
}
