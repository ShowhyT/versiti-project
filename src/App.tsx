import { useState, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
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

const TAB_PATHS: TabId[] = ['home', 'schedule', 'maps', 'passes', 'grades', 'esports']

function MainLayout({ onLogout }: { onLogout: () => void }) {
  const navigate = useNavigate()
  const location = useLocation()

  const currentTab = (location.pathname.slice(1) as TabId) || 'home'
  const activeTab = TAB_PATHS.includes(currentTab) ? currentTab : 'home'

  const renderPage = () => {
    switch (activeTab) {
      case 'home':
        return (
          <HomePage
            onOpenProfile={() => navigate('/profile')}
            onOpenFriends={() => navigate('/friends')}
          />
        )
      case 'schedule':
        return <SchedulePage />
      case 'maps':
        return <MapsPage />
      case 'passes':
        return <PassesPage />
      case 'grades':
        return <GradesPage />
      case 'esports':
        return <EsportsPage />
    }
  }

  // Attach logout to profile when it's rendered there
  void onLogout

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
          {renderPage()}
        </motion.div>
      </AnimatePresence>
      <TabBar active={activeTab} onChange={(tab) => navigate(`/${tab}`)} />
    </>
  )
}

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(() => !!getToken())

  const handleLogin = useCallback(() => {
    setIsLoggedIn(true)
  }, [])

  const handleLogout = useCallback(() => {
    setToken(null)
    setIsLoggedIn(false)
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/privacy"
          element={<PrivacyPageWrapper />}
        />
        {!isLoggedIn ? (
          <>
            <Route
              path="/"
              element={<LoginPageWrapper onLogin={handleLogin} />}
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </>
        ) : (
          <>
            <Route path="/profile" element={<ProfilePageWrapper onLogout={handleLogout} />} />
            <Route path="/friends" element={<FriendsPageWrapper />} />
            <Route path="/home" element={<MainLayout onLogout={handleLogout} />} />
            <Route path="/schedule" element={<MainLayout onLogout={handleLogout} />} />
            <Route path="/maps" element={<MainLayout onLogout={handleLogout} />} />
            <Route path="/passes" element={<MainLayout onLogout={handleLogout} />} />
            <Route path="/grades" element={<MainLayout onLogout={handleLogout} />} />
            <Route path="/esports" element={<MainLayout onLogout={handleLogout} />} />
            <Route path="*" element={<Navigate to="/home" replace />} />
          </>
        )}
      </Routes>
    </BrowserRouter>
  )
}

function LoginPageWrapper({ onLogin }: { onLogin: () => void }) {
  const navigate = useNavigate()
  return <LoginPage onLogin={() => { onLogin(); navigate('/home') }} onOpenPrivacy={() => navigate('/privacy')} />
}

function PrivacyPageWrapper() {
  const navigate = useNavigate()
  return <PrivacyPage onClose={() => navigate(-1)} />
}

function ProfilePageWrapper({ onLogout }: { onLogout: () => void }) {
  const navigate = useNavigate()
  return (
    <ProfilePage
      onClose={() => navigate('/home')}
      onLogout={() => { onLogout(); navigate('/') }}
    />
  )
}

function FriendsPageWrapper() {
  const navigate = useNavigate()
  return <FriendsPage onClose={() => navigate('/home')} />
}
