import { useState } from 'react'
import AppLayout from '../layouts/AppLayout'
import Profile   from './tabs/Profile'
import Users     from './tabs/Users'
import Scans     from './tabs/Scans'
import Incidents from './tabs/Incidents'
import Reports   from './tabs/Reports'
import Mobile    from './tabs/Mobile'
import Ebios     from './tabs/Ebios'
import AI        from './tabs/AI'
import Logs      from './tabs/Logs'

export default function Dashboard() {
  const [tab, setTab]                 = useState('profile')
  const [pendingAnalyze, setPending]  = useState(null)

  const handleAnalyzeAI = (type, id) => {
    setPending({ type, id })
    setTab('ai')
  }

  const handleTabChange = (newTab) => {
    setTab(newTab)
  }

  const renderTab = () => {
    switch (tab) {
      case 'profile':   return <Profile />
      case 'users':     return <Users />
      case 'scans':     return <Scans onAnalyzeAI={handleAnalyzeAI} />
      case 'incidents': return <Incidents onAnalyzeAI={handleAnalyzeAI} />
      case 'reports':   return <Reports />
      case 'mobile':    return <Mobile />
      case 'ebios':     return <Ebios />
      case 'ai':        return <AI pendingAnalyze={pendingAnalyze} onAnalyzeDone={() => setPending(null)} />
      case 'logs':      return <Logs />
      default:          return <Profile />
    }
  }

  return (
    <AppLayout activeTab={tab} onTabChange={handleTabChange}>
      {renderTab()}
    </AppLayout>
  )
}
