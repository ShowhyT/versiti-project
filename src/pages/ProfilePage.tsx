import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { slideUp, spring } from '../lib/motion'
import {
  User,
  LogOut,
  Link,
  Unlink,
  Loader2,
  Eye,
  EyeOff,
  Shield,
} from 'lucide-react'
import { api, setToken } from '../lib/api'

interface Profile {
  id: number
  username: string
  full_name: string
  mirea_login: string | null
  mirea_connected: boolean
  last_mirea_sync_at: string | null
  esports_connected: boolean
  created_at: string | null
  settings: {
    mark_with_friends_default: boolean
    auto_select_favorites: boolean
    haptics_enabled: boolean
    theme_mode: string | null
  }
}

interface Props {
  onClose: () => void
  onLogout: () => void
}

export default function ProfilePage({ onClose, onLogout }: Props) {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // MIREA connect form
  const [showConnect, setShowConnect] = useState(false)
  const [mireLogin, setMireLogin] = useState('')
  const [mirePassword, setMirePassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [connectLoading, setConnectLoading] = useState(false)
  const [connectMsg, setConnectMsg] = useState<string | null>(null)

  // 2FA state
  const [needs2fa, setNeeds2fa] = useState(false)
  const [otpState, setOtpState] = useState('')
  const [otpCode, setOtpCode] = useState('')

  const fetchProfile = useCallback(async () => {
    try {
      const res = await api<{ success: boolean; profile: Profile }>('/api/profile')
      if (res.success) setProfile(res.profile)
    } catch {
      setError('Не удалось загрузить профиль')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchProfile()
  }, [fetchProfile])

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!mireLogin.trim() || !mirePassword.trim()) return
    setConnectLoading(true)
    setConnectMsg(null)

    try {
      const res = await api<{
        success: boolean
        message?: string
        needs_2fa?: boolean
        state?: string
      }>('/api/auth/mirea-connect', {
        method: 'POST',
        body: JSON.stringify({ login: mireLogin.trim(), password: mirePassword }),
      })

      if (res.success) {
        setConnectMsg('МИРЭА подключён')
        setShowConnect(false)
        setMireLogin('')
        setMirePassword('')
        fetchProfile()
      } else if (res.needs_2fa && res.state) {
        setNeeds2fa(true)
        setOtpState(res.state)
      } else {
        setConnectMsg(res.message || 'Ошибка подключения')
      }
    } catch {
      setConnectMsg('Не удалось подключиться')
    } finally {
      setConnectLoading(false)
    }
  }

  const handleOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!otpCode.trim()) return
    setConnectLoading(true)

    try {
      const res = await api<{ success: boolean; message?: string }>('/api/auth/mirea-2fa', {
        method: 'POST',
        body: JSON.stringify({ state: otpState, code: otpCode.trim() }),
      })

      if (res.success) {
        setConnectMsg('МИРЭА подключён')
        setNeeds2fa(false)
        setShowConnect(false)
        setOtpCode('')
        setMireLogin('')
        setMirePassword('')
        fetchProfile()
      } else {
        setConnectMsg(res.message || 'Неверный код')
      }
    } catch {
      setConnectMsg('Ошибка')
    } finally {
      setConnectLoading(false)
    }
  }

  const handleDisconnect = async () => {
    try {
      await api('/api/auth/mirea-disconnect', { method: 'POST' })
      fetchProfile()
    } catch { /* ignore */ }
  }

  const handleLogout = async () => {
    try {
      await api('/api/auth/logout', { method: 'POST' })
    } catch { /* ignore */ }
    setToken(null)
    onLogout()
  }

  const inputClass =
    'w-full px-4 py-3 bg-surface-1 border border-border rounded-xl text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-border-active transition-colors'

  if (loading) {
    return (
      <div className="flex-1 flex justify-center items-center">
        <Loader2 size={24} className="animate-spin text-brand" />
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <motion.div variants={slideUp} initial="enter" animate="active" className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-text-primary">Профиль</h1>
          <button onClick={onClose} className="text-sm text-brand">Назад</button>
        </div>

        {error && (
          <div className="bg-danger/10 text-danger text-sm rounded-xl p-4 text-center">{error}</div>
        )}

        {profile && (
          <>
            {/* User card */}
            <div className="bg-surface-2 rounded-xl border border-border p-5 flex items-center gap-4">
              <div className="w-14 h-14 bg-brand-glow rounded-full flex items-center justify-center">
                <User size={28} className="text-brand" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-lg font-semibold text-text-primary truncate">{profile.full_name}</p>
                <p className="text-sm text-text-secondary">@{profile.username}</p>
              </div>
            </div>

            {/* MIREA connection */}
            <div className="space-y-2">
              <h2 className="text-sm font-medium text-text-secondary px-1">МИРЭА</h2>
              <div className="bg-surface-2 rounded-xl border border-border overflow-hidden">
                <div className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Shield size={18} className={profile.mirea_connected ? 'text-success' : 'text-text-muted'} />
                    <div>
                      <p className="text-sm font-medium text-text-primary">
                        {profile.mirea_connected ? 'Подключено' : 'Не подключено'}
                      </p>
                      {profile.mirea_login && (
                        <p className="text-xs text-text-secondary">{profile.mirea_login}</p>
                      )}
                    </div>
                  </div>
                  {profile.mirea_connected ? (
                    <button
                      onClick={handleDisconnect}
                      className="flex items-center gap-1 text-xs text-danger hover:text-danger/80 transition-colors"
                    >
                      <Unlink size={14} />
                      Отвязать
                    </button>
                  ) : (
                    <button
                      onClick={() => setShowConnect(true)}
                      className="flex items-center gap-1 text-xs text-brand hover:text-brand-light transition-colors"
                    >
                      <Link size={14} />
                      Привязать
                    </button>
                  )}
                </div>

                {/* Connect form */}
                <AnimatePresence>
                  {showConnect && !needs2fa && (
                    <motion.form
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      onSubmit={handleConnect}
                      className="overflow-hidden border-t border-border"
                    >
                      <div className="p-4 space-y-3">
                        <input
                          type="text"
                          placeholder="Логин МИРЭА"
                          value={mireLogin}
                          onChange={(e) => setMireLogin(e.target.value)}
                          className={inputClass}
                        />
                        <div className="relative">
                          <input
                            type={showPassword ? 'text' : 'password'}
                            placeholder="Пароль МИРЭА"
                            value={mirePassword}
                            onChange={(e) => setMirePassword(e.target.value)}
                            className={`${inputClass} pr-12`}
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
                            onClick={() => setShowConnect(false)}
                            className="flex-1 py-2.5 bg-surface-1 border border-border rounded-xl text-sm text-text-secondary"
                          >
                            Отмена
                          </button>
                          <motion.button
                            type="submit"
                            disabled={connectLoading}
                            whileTap={{ scale: 0.97 }}
                            className="flex-1 py-2.5 bg-brand text-white rounded-xl text-sm font-medium disabled:opacity-50"
                          >
                            {connectLoading ? <Loader2 size={16} className="animate-spin mx-auto" /> : 'Подключить'}
                          </motion.button>
                        </div>
                      </div>
                    </motion.form>
                  )}

                  {needs2fa && (
                    <motion.form
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      onSubmit={handleOtp}
                      className="overflow-hidden border-t border-border"
                    >
                      <div className="p-4 space-y-3">
                        <input
                          type="text"
                          placeholder="Код подтверждения"
                          value={otpCode}
                          onChange={(e) => setOtpCode(e.target.value)}
                          inputMode="numeric"
                          autoFocus
                          className={inputClass}
                        />
                        <motion.button
                          type="submit"
                          disabled={connectLoading}
                          whileTap={{ scale: 0.97 }}
                          className="w-full py-2.5 bg-brand text-white rounded-xl text-sm font-medium disabled:opacity-50"
                        >
                          {connectLoading ? <Loader2 size={16} className="animate-spin mx-auto" /> : 'Подтвердить'}
                        </motion.button>
                      </div>
                    </motion.form>
                  )}
                </AnimatePresence>
              </div>

              {connectMsg && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className={`text-xs px-1 ${connectMsg.includes('подключён') ? 'text-success' : 'text-danger'}`}
                >
                  {connectMsg}
                </motion.p>
              )}
            </div>

            {/* Settings */}
            <div className="space-y-2">
              <h2 className="text-sm font-medium text-text-secondary px-1">Настройки</h2>
              <div className="bg-surface-2 rounded-xl border border-border divide-y divide-border">
                <ToggleRow
                  label="Отмечать с друзьями"
                  description="По умолчанию при сканировании QR"
                  value={profile.settings.mark_with_friends_default}
                  onChange={async (v) => {
                    await api('/api/profile', {
                      method: 'PATCH',
                      body: JSON.stringify({ mark_with_friends_default: v }),
                    })
                    setProfile((p) => p ? { ...p, settings: { ...p.settings, mark_with_friends_default: v } } : p)
                  }}
                />
                <ToggleRow
                  label="Автовыбор избранных"
                  description="Автоматически выбирать избранных друзей"
                  value={profile.settings.auto_select_favorites}
                  onChange={async (v) => {
                    await api('/api/profile', {
                      method: 'PATCH',
                      body: JSON.stringify({ auto_select_favorites: v }),
                    })
                    setProfile((p) => p ? { ...p, settings: { ...p.settings, auto_select_favorites: v } } : p)
                  }}
                />
              </div>
            </div>

            {/* Account info */}
            <div className="space-y-2">
              <h2 className="text-sm font-medium text-text-secondary px-1">Аккаунт</h2>
              <div className="bg-surface-2 rounded-xl border border-border divide-y divide-border">
                {profile.created_at && (
                  <div className="px-4 py-3 flex justify-between">
                    <span className="text-sm text-text-secondary">Создан</span>
                    <span className="text-sm text-text-primary">
                      {new Date(profile.created_at).toLocaleDateString('ru-RU')}
                    </span>
                  </div>
                )}
                {profile.last_mirea_sync_at && (
                  <div className="px-4 py-3 flex justify-between">
                    <span className="text-sm text-text-secondary">Последняя синхр.</span>
                    <span className="text-sm text-text-primary">
                      {new Date(profile.last_mirea_sync_at).toLocaleString('ru-RU')}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Logout */}
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 py-3 bg-danger/10 text-danger rounded-xl text-sm font-medium"
            >
              <LogOut size={16} />
              Выйти из аккаунта
            </motion.button>
          </>
        )}
      </motion.div>
    </div>
  )
}

function ToggleRow({
  label,
  description,
  value,
  onChange,
}: {
  label: string
  description: string
  value: boolean
  onChange: (v: boolean) => void
}) {
  const [checked, setChecked] = useState(value)

  return (
    <button
      onClick={() => {
        const next = !checked
        setChecked(next)
        onChange(next)
      }}
      className="w-full px-4 py-3 flex items-center justify-between text-left"
    >
      <div>
        <p className="text-sm font-medium text-text-primary">{label}</p>
        <p className="text-xs text-text-muted mt-0.5">{description}</p>
      </div>
      <div
        className={`w-10 h-6 rounded-full relative transition-colors ${
          checked ? 'bg-brand' : 'bg-surface-3'
        }`}
      >
        <motion.div
          animate={{ x: checked ? 18 : 2 }}
          transition={spring}
          className="absolute top-1 w-4 h-4 bg-white rounded-full shadow"
        />
      </div>
    </button>
  )
}
