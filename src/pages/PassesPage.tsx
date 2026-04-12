import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { slideUp, spring } from '../lib/motion'
import { RefreshCw, Loader2, DoorOpen, DoorClosed, BookOpen } from 'lucide-react'
import { api } from '../lib/api'
import type { AcsEvent, AcsResponse } from '../lib/types'

function EventRow({ event, index }: { event: AcsEvent; index: number }) {
  const hasEnter = !!event.enter_zone
  const hasExit = !!event.exit_zone

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="flex items-center gap-3 bg-surface-2 rounded-xl border border-border p-4"
    >
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
          hasEnter ? 'bg-success/15' : 'bg-danger/15'
        }`}
      >
        {hasEnter ? (
          <DoorOpen size={20} className="text-success" />
        ) : (
          <DoorClosed size={20} className="text-danger" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-text-primary">
            {event.time}
          </span>
          {event.duration && event.duration !== '—' && (
            <span className="text-xs text-text-muted">{event.duration}</span>
          )}
        </div>
        <p className="text-xs text-text-secondary truncate mt-0.5">
          {hasEnter && event.enter_zone}
          {hasEnter && hasExit && ' → '}
          {hasExit && event.exit_zone}
          {!hasEnter && !hasExit && 'Неизвестная зона'}
        </p>
      </div>
    </motion.div>
  )
}

export default function PassesPage() {
  const [events, setEvents] = useState<AcsEvent[]>([])
  const [date, setDate] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [needsAuth, setNeedsAuth] = useState(false)

  const fetchEvents = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api<AcsResponse>('/api/acs/events')
      if (res.success) {
        setEvents(res.events)
        setDate(res.date)
        setNeedsAuth(false)
      } else if (res.needs_auth) {
        setNeedsAuth(true)
      } else {
        setError(res.message || 'Ошибка загрузки')
      }
    } catch {
      setError('Не удалось загрузить данные')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchEvents()
  }, [fetchEvents])

  const formattedDate = date
    ? new Date(date + 'T00:00:00').toLocaleDateString('ru-RU', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
      })
    : ''

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <motion.div variants={slideUp} initial="enter" animate="active" className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-text-primary">Пропуск</h1>
            {formattedDate && (
              <p className="text-xs text-text-secondary mt-0.5 capitalize">{formattedDate}</p>
            )}
          </div>
          <button
            onClick={fetchEvents}
            disabled={loading}
            className="p-2 text-text-muted hover:text-brand transition-colors"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {needsAuth && (
          <div className="bg-surface-2 rounded-xl border border-border p-4 flex items-center gap-3">
            <BookOpen size={20} className="text-brand shrink-0" />
            <p className="text-sm text-text-secondary">
              Подключите аккаунт МИРЭА в профиле для просмотра проходов
            </p>
          </div>
        )}

        {loading && events.length === 0 && (
          <div className="flex justify-center py-12">
            <Loader2 size={24} className="animate-spin text-brand" />
          </div>
        )}

        {error && (
          <div className="bg-danger/10 text-danger text-sm rounded-xl p-4 text-center">{error}</div>
        )}

        {/* Summary */}
        {events.length > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={spring}
            className="bg-surface-2 rounded-xl border border-border p-4 flex items-center justify-between"
          >
            <div>
              <p className="text-xs text-text-muted">Проходов за день</p>
              <p className="text-2xl font-bold text-text-primary tabular-nums">{events.length}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-text-muted">Последний</p>
              <p className="text-lg font-medium text-text-primary">
                {events[events.length - 1]?.time || '—'}
              </p>
            </div>
          </motion.div>
        )}

        {/* Events list */}
        {events.length > 0 && (
          <div className="space-y-2">
            {events.map((ev, i) => (
              <EventRow key={ev.ts || i} event={ev} index={i} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && !needsAuth && !error && events.length === 0 && date && (
          <div className="text-center py-12">
            <DoorOpen size={48} className="mx-auto text-text-muted mb-3" />
            <p className="text-sm text-text-secondary">Нет проходов за сегодня</p>
          </div>
        )}
      </motion.div>
    </div>
  )
}
