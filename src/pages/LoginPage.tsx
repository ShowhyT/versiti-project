import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { scaleIn, spring, slideUp } from '../lib/motion'
import { Eye, EyeOff, LogIn, Loader2, KeyRound, ArrowLeft, Code2 } from 'lucide-react'
import { api, setToken } from '../lib/api'

type Step = 'credentials' | '2fa'

interface Props {
  onLogin: () => void
  onOpenPrivacy: () => void
}

export default function LoginPage({ onLogin, onOpenPrivacy }: Props) {
  const [step, setStep] = useState<Step>('credentials')
  const [login, setLogin] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [otpCode, setOtpCode] = useState('')
  const [state, setState] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [privacyAccepted, setPrivacyAccepted] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!login.trim() || !password.trim() || !privacyAccepted) return
    setLoading(true)
    setError(null)

    try {
      const res = await api<{
        success: boolean
        token?: string
        needs_2fa?: boolean
        state?: string
        message?: string
      }>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ login: login.trim(), password }),
      })

      if (res.success && res.token) {
        setToken(res.token)
        onLogin()
      } else if (res.needs_2fa && res.state) {
        setState(res.state)
        setStep('2fa')
      } else {
        setError(res.message || 'Ошибка авторизации')
      }
    } catch {
      setError('Не удалось подключиться к серверу')
    } finally {
      setLoading(false)
    }
  }

  const handleOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!otpCode.trim()) return
    setLoading(true)
    setError(null)

    try {
      const res = await api<{
        success: boolean
        token?: string
        needs_2fa?: boolean
        state?: string
        message?: string
      }>('/api/auth/2fa', {
        method: 'POST',
        body: JSON.stringify({ state, code: otpCode.trim() }),
      })

      if (res.success && res.token) {
        setToken(res.token)
        onLogin()
      } else {
        setError(res.message || 'Неверный код')
      }
    } catch {
      setError('Не удалось подключиться к серверу')
    } finally {
      setLoading(false)
    }
  }

  const inputClass =
    'w-full px-4 py-3 bg-surface-2 border border-border rounded-xl text-text-primary placeholder:text-text-muted focus:outline-none focus:border-border-active transition-colors'

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6">
      <motion.div
        variants={scaleIn}
        initial="enter"
        animate="active"
        transition={spring}
        className="w-full max-w-sm space-y-8"
      >
        {/* Logo */}
        <div className="text-center space-y-2">
          <div className="w-16 h-16 bg-brand-glow rounded-2xl flex items-center justify-center mx-auto">
            <div className="w-8 h-8 bg-brand rounded-lg" />
          </div>
          <h1 className="text-2xl font-bold text-text-primary mt-4">Versiti</h1>
          <p className="text-sm text-text-secondary">
            {step === 'credentials' ? 'Войдите через аккаунт lk.mirea.ru' : 'Введите код подтверждения'}
          </p>
        </div>

        <AnimatePresence mode="wait">
          {step === 'credentials' && (
            <motion.form
              key="credentials"
              variants={slideUp}
              initial="enter"
              animate="active"
              exit="exit"
              onSubmit={handleLogin}
              className="space-y-4"
            >
              <div className="space-y-3">
                <input
                  type="text"
                  placeholder="Логин МИРЭА"
                  value={login}
                  onChange={(e) => setLogin(e.target.value)}
                  autoComplete="username"
                  className={inputClass}
                />
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Пароль"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    className={`${inputClass} pr-12`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {/* Privacy checkbox */}
              <div className="flex items-start gap-3">
                <button
                  type="button"
                  onClick={() => setPrivacyAccepted(!privacyAccepted)}
                  className={`mt-0.5 w-5 h-5 shrink-0 rounded border-2 flex items-center justify-center transition-colors ${
                    privacyAccepted
                      ? 'bg-brand border-brand'
                      : 'bg-transparent border-border hover:border-text-muted'
                  }`}
                >
                  {privacyAccepted && (
                    <motion.svg
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      width="12"
                      height="12"
                      viewBox="0 0 12 12"
                      fill="none"
                    >
                      <path
                        d="M2 6L5 9L10 3"
                        stroke="white"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </motion.svg>
                  )}
                </button>
                <span className="text-xs text-text-secondary leading-relaxed">
                  Я соглашаюсь с{' '}
                  <button
                    type="button"
                    onClick={onOpenPrivacy}
                    className="text-brand hover:underline"
                  >
                    политикой конфиденциальности
                  </button>
                </span>
              </div>

              {error && (
                <motion.p
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-sm text-danger text-center"
                >
                  {error}
                </motion.p>
              )}

              <motion.button
                type="submit"
                disabled={loading || !login.trim() || !password.trim() || !privacyAccepted}
                whileTap={{ scale: 0.97 }}
                className="w-full flex items-center justify-center gap-2 py-3 bg-brand hover:bg-brand-dark disabled:opacity-50 text-white font-medium rounded-xl transition-colors"
              >
                {loading ? (
                  <Loader2 size={20} className="animate-spin" />
                ) : (
                  <>
                    <LogIn size={18} />
                    Войти
                  </>
                )}
              </motion.button>
            </motion.form>
          )}

          {step === '2fa' && (
            <motion.form
              key="2fa"
              variants={slideUp}
              initial="enter"
              animate="active"
              exit="exit"
              onSubmit={handleOtp}
              className="space-y-4"
            >
              <input
                type="text"
                placeholder="Код подтверждения"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                autoComplete="one-time-code"
                inputMode="numeric"
                className={inputClass}
                autoFocus
              />

              {error && (
                <motion.p
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-sm text-danger text-center"
                >
                  {error}
                </motion.p>
              )}

              <motion.button
                type="submit"
                disabled={loading || !otpCode.trim()}
                whileTap={{ scale: 0.97 }}
                className="w-full flex items-center justify-center gap-2 py-3 bg-brand hover:bg-brand-dark disabled:opacity-50 text-white font-medium rounded-xl transition-colors"
              >
                {loading ? (
                  <Loader2 size={20} className="animate-spin" />
                ) : (
                  <>
                    <KeyRound size={18} />
                    Подтвердить
                  </>
                )}
              </motion.button>

              <button
                type="button"
                onClick={() => {
                  setStep('credentials')
                  setOtpCode('')
                  setError(null)
                }}
                className="w-full flex items-center justify-center gap-1 text-sm text-text-secondary hover:text-text-primary transition-colors"
              >
                <ArrowLeft size={14} />
                Назад
              </button>
            </motion.form>
          )}
        </AnimatePresence>

        {/* Footer */}
        <div className="space-y-3">
          <p className="text-xs text-text-muted text-center leading-relaxed">
            Пароль не сохраняется — используется только для получения сессии
          </p>
          <a
            href="https://github.com/silverhans/versiti-project"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 text-xs text-text-muted hover:text-text-secondary transition-colors"
          >
            <Code2 size={14} />
            Open Source Project
          </a>
        </div>
      </motion.div>
    </div>
  )
}
