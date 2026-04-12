import { useState, useCallback } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import TabBar from './components/TabBar'
import LoginPage from './pages/LoginPage'
import HomePage from './pages/HomePage'
import SchedulePage from './pages/SchedulePage'
import MapsPage from './pages/MapsPage'
import PassesPage from './pages/PassesPage'
import GradesPage from './pages/GradesPage'
import EsportsPage from './pages/EsportsPage'
import ProfilePage from './pages/ProfilePage'
import FriendsPage from './pages/FriendsPage'
import PrivacyPage from './pages/PrivacyPage'
import { getToken, setToken } from './lib/api'

export type TabId = 'home' | 'schedule' | 'maps' | 'passes' | 'grades' | 'esports'

type Overlay = 'profile' | 'friends' | 'privacy' | null

const PAGES: Record<TabId, React.FC<{ onOpenProfile?: () => void; onOpenFriends?: () => void }>> = {
  home: HomePage,
  schedule: SchedulePage,
  maps: MapsPage,
  passes: PassesPage,
  grades: GradesPage,
  esports: EsportsPage,
}

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(() => !!getToken())
  const [activeTab, setActiveTab] = useState<TabId>('home')
  const [overlay, setOverlay] = useState<Overlay>(null)

  const handleLogin = useCallback(() => {
    setIsLoggedIn(true)
  }, [])

  const handleLogout = useCallback(() => {
    setToken(null)
    setIsLoggedIn(false)
    setOverlay(null)
  }, [])

  if (overlay === 'privacy') {
    return <PrivacyPage onClose={() => setOverlay(null)} />
  }

  if (!isLoggedIn) {
    return (
      <LoginPage
        onLogin={handleLogin}
        onOpenPrivacy={() => setOverlay('privacy')}
      />
    )
  }

  if (overlay === 'profile') {
    return (
      <ProfilePage
        onClose={() => setOverlay(null)}
        onLogout={handleLogout}
      />
    )
  }

  if (overlay === 'friends') {
    return <FriendsPage onClose={() => setOverlay(null)} />
  }

  const Page = PAGES[activeTab]

  return (
    <>
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className="flex-1 overflow-hidden"
        >
          <Page
            onOpenProfile={() => setOverlay('profile')}
            onOpenFriends={() => setOverlay('friends')}
          />
        </motion.div>
      </AnimatePresence>
      <TabBar active={activeTab} onChange={setActiveTab} />
    </>
  )
}
