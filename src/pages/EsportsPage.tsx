import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { slideUp, spring } from '../lib/motion'
import {
  Loader2,
  LogIn,
  LogOut,
  Calendar,
  Clock,
  Monitor,
  X,
  Eye,
  EyeOff,
} from 'lucide-react'
import { api } from '../lib/api'

interface Booking {
  id: string
  device_name?: string
  booking_datetime: string
  booking_duration: number
  status?: string
}

export default function EsportsPage() {
  const [authorized, setAuthorized] = useState<boolean | null>(null)
  const [bookings, setBookings] = useState<Booking[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Login form
  const [showLogin, setShowLogin] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loginLoading, setLoginLoading] = useState(false)

  const checkStatus = useCallback(async () => {
    try {
      const res = await api<{ success: boolean; authorized: boolean }>('/api/esports/status')
      setAuthorized(res.authorized)
      if (res.authorized) {
        const bRes = await api<{ success: boolean; data?: { bookings?: Booking[] } }>(
          '/api/esports/bookings',
        )
        if (bRes.success && bRes.data?.bookings) {
          setBookings(bRes.data.bookings)
        }
      }
    } catch {
      setError('Не удалось проверить статус')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    checkStatus()
  }, [checkStatus])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password.trim()) return
    setLoginLoading(true)
    setError(null)

    try {
      const res = await api<{ success: boolean; message: string }>('/api/esports/login', {
        method: 'POST',
        body: JSON.stringify({ email: email.trim(), password }),
      })
      if (res.success) {
        setAuthorized(true)
        setShowLogin(false)
        setEmail('')
        setPassword('')
        checkStatus()
      } else {
        setError(res.message)
      }
    } catch {
      setError('Ошибка авторизации')
    } finally {
      setLoginLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      await api('/api/esports/logout', { method: 'POST' })
      setAuthorized(false)
      setBookings([])
    } catch {
      /* ignore */
    }
  }

  const handleCancel = async (bookingId: string) => {
    try {
      const res = await api<{ success: boolean; message?: string }>('/api/esports/cancel', {
        method: 'POST',
        body: JSON.stringify({ booking_id: bookingId }),
      })
      if (res.success) {
        setBookings((prev) => prev.filter((b) => b.id !== bookingId))
      }
    } catch {
      /* ignore */
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex justify-center items-center">
        <Loader2 size={24} className="animate-spin text-brand" />
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <motion.div variants={slideUp} initial="enter" animate="active" className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-text-primary">Киберзона</h1>
          {authorized && (
            <button
              onClick={handleLogout}
              className="flex items-center gap-1 text-xs text-text-muted hover:text-danger transition-colors"
            >
              <LogOut size={14} />
              Выйти
            </button>
          )}
        </div>

        {error && (
          <div className="bg-danger/10 text-danger text-sm rounded-xl p-4 text-center">{error}</div>
        )}

        {/* Not authorized */}
        {!authorized && !showLogin && (
          <div className="text-center space-y-4 py-8">
            <Monitor size={48} className="mx-auto text-text-muted" />
            <p className="text-sm text-text-secondary">
              Войдите в аккаунт киберзоны для бронирования
            </p>
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={() => setShowLogin(true)}
              className="inline-flex items-center gap-2 px-6 py-3 bg-brand text-white rounded-xl text-sm font-medium"
            >
              <LogIn size={16} />
              Войти
            </motion.button>
          </div>
        )}

        {/* Login form */}
        <AnimatePresence>
          {showLogin && (
            <motion.form
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 12 }}
              onSubmit={handleLogin}
              className="bg-surface-2 rounded-xl border border-border p-4 space-y-3"
            >
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-surface-1 border border-border rounded-xl text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-border-active transition-colors"
              />
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Пароль"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 pr-12 bg-surface-1 border border-border rounded-xl text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-border-active transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowLogin(false)}
                  className="flex-1 py-2.5 bg-surface-1 border border-border rounded-xl text-sm text-text-secondary"
                >
                  Отмена
                </button>
                <motion.button
                  type="submit"
                  disabled={loginLoading}
                  whileTap={{ scale: 0.97 }}
                  className="flex-1 py-2.5 bg-brand text-white rounded-xl text-sm font-medium disabled:opacity-50"
                >
                  {loginLoading ? <Loader2 size={16} className="animate-spin mx-auto" /> : 'Войти'}
                </motion.button>
              </div>
            </motion.form>
          )}
        </AnimatePresence>

        {/* Bookings */}
        {authorized && (
          <>
            <div className="text-sm text-text-secondary">
              {bookings.length > 0 ? 'Ваши бронирования:' : 'Нет активных бронирований'}
            </div>

            <div className="space-y-3">
              {bookings.map((b) => (
                <motion.div
                  key={b.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={spring}
                  className="bg-surface-2 rounded-xl border border-border p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Monitor size={16} className="text-brand" />
                      <span className="text-sm font-medium text-text-primary">
                        {b.device_name || 'Место'}
                      </span>
                    </div>
                    <button
                      onClick={() => handleCancel(b.id)}
                      className="p-1 text-text-muted hover:text-danger transition-colors"
                    >
                      <X size={14} />
                    </button>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-text-secondary">
                    <span className="flex items-center gap-1">
                      <Calendar size={12} />
                      {new Date(b.booking_datetime).toLocaleDateString('ru-RU')}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock size={12} />
                      {new Date(b.booking_datetime).toLocaleTimeString('ru-RU', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                      {' · '}
                      {b.booking_duration} мин
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </>
        )}
      </motion.div>
    </div>
  )
}
