import { useState, useEffect, useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { slideUp, spring } from '../lib/motion'
import { Clock, MapPin, ChevronLeft, ChevronRight, Loader2, RefreshCw, BookOpen } from 'lucide-react'
import { api } from '../lib/api'
import type { ScheduleEvent } from '../lib/types'

function formatTime(iso: string) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

function formatDateLabel(date: Date) {
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(today.getDate() + 1)

  const isToday = date.toDateString() === today.toDateString()
  const isTomorrow = date.toDateString() === tomorrow.toDateString()

  const label = date.toLocaleDateString('ru-RU', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  })

  if (isToday) return `Сегодня, ${label}`
  if (isTomorrow) return `Завтра, ${label}`
  return label.charAt(0).toUpperCase() + label.slice(1)
}

function localDayKey(d: Date) {
  // Local date key (YYYY-MM-DD), not UTC
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function groupEventsByDay(events: ScheduleEvent[]) {
  const days = new Map<string, ScheduleEvent[]>()
  for (const ev of events) {
    if (!ev.start) continue
    const dateKey = localDayKey(new Date(ev.start))
    if (!days.has(dateKey)) days.set(dateKey, [])
    days.get(dateKey)!.push(ev)
  }
  return days
}

function EventCard({ event }: { event: ScheduleEvent }) {
  const lines = event.description.split('\n').filter(Boolean)
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface-2 rounded-xl border border-border p-4 space-y-2"
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-medium text-text-primary leading-snug flex-1">
          {event.summary}
        </h3>
        {event.start && (
          <div className="flex items-center gap-1 text-xs text-brand shrink-0">
            <Clock size={12} />
            {formatTime(event.start)}
            {event.end && ` – ${formatTime(event.end)}`}
          </div>
        )}
      </div>
      {event.location && (
        <div className="flex items-center gap-1 text-xs text-text-secondary">
          <MapPin size={12} />
          {event.location}
        </div>
      )}
      {lines.length > 0 && (
        <p className="text-xs text-text-muted leading-relaxed">
          {lines.join(' · ')}
        </p>
      )}
    </motion.div>
  )
}

export default function SchedulePage() {
  const [events, setEvents] = useState<ScheduleEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [needsAuth, setNeedsAuth] = useState(false)
  const [focusDate, setFocusDate] = useState(() => new Date())

  const fetchSchedule = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api<{
        success: boolean
        events: ScheduleEvent[]
        message?: string
        needs_auth?: boolean
      }>('/api/schedule/pulse?days=14')
      if (res.success) {
        setEvents(res.events)
        setNeedsAuth(false)
      } else if (res.needs_auth) {
        setNeedsAuth(true)
      } else {
        setError(res.message || 'Ошибка загрузки')
      }
    } catch {
      setError('Не удалось загрузить расписание')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSchedule()
  }, [fetchSchedule])

  const eventsByDay = useMemo(() => groupEventsByDay(events), [events])

  const focusKey = localDayKey(focusDate)
  const dayEvents: ScheduleEvent[] = eventsByDay.get(focusKey) || []
  const allDays = [...eventsByDay.keys()].sort()

  // Auto-focus first day with events if current has none
  useEffect(() => {
    if (allDays.length === 0) return
    if (!allDays.includes(focusKey)) {
      // Pick today if present, else first upcoming day, else first
      const todayKey = localDayKey(new Date())
      const upcoming = allDays.find((d) => d >= todayKey)
      setFocusDate(new Date(upcoming || allDays[0] + 'T00:00:00'))
    }
  }, [allDays, focusKey])

  const shiftDay = (dir: number) => {
    const idx = allDays.indexOf(focusKey)
    if (idx === -1) {
      if (allDays.length === 0) return
      setFocusDate(new Date(allDays[0] + 'T00:00:00'))
    } else {
      const nextIdx = Math.max(0, Math.min(allDays.length - 1, idx + dir))
      setFocusDate(new Date(allDays[nextIdx] + 'T00:00:00'))
    }
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <motion.div variants={slideUp} initial="enter" animate="active" className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-text-primary">Расписание</h1>
          <button
            onClick={fetchSchedule}
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
              Подключите аккаунт МИРЭА в профиле для просмотра расписания
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

        {!loading && allDays.length > 0 && (
          <>
            <div className="flex items-center justify-between">
              <button onClick={() => shiftDay(-1)} className="p-2 text-text-muted hover:text-text-primary transition-colors">
                <ChevronLeft size={20} />
              </button>
              <motion.span
                key={focusKey}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-sm font-medium text-text-primary"
              >
                {formatDateLabel(focusDate)}
              </motion.span>
              <button onClick={() => shiftDay(1)} className="p-2 text-text-muted hover:text-text-primary transition-colors">
                <ChevronRight size={20} />
              </button>
            </div>

            <div className="flex justify-center gap-1.5 flex-wrap">
              {allDays.map((d) => (
                <button
                  key={d}
                  onClick={() => setFocusDate(new Date(d + 'T00:00:00'))}
                  className="relative"
                >
                  <div
                    className={`w-2 h-2 rounded-full transition-colors ${
                      d === focusKey ? 'bg-brand' : 'bg-surface-3'
                    }`}
                  />
                  {d === focusKey && (
                    <motion.div
                      layoutId="dayDot"
                      className="absolute inset-0 w-2 h-2 rounded-full bg-brand"
                      transition={spring}
                    />
                  )}
                </button>
              ))}
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={focusKey}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
                className="space-y-3"
              >
                {dayEvents.length > 0 ? (
                  dayEvents.map((ev, i) => <EventCard key={i} event={ev} />)
                ) : (
                  <p className="text-sm text-text-muted text-center py-8">Нет пар в этот день</p>
                )}
              </motion.div>
            </AnimatePresence>
          </>
        )}

        {!loading && !needsAuth && !error && events.length === 0 && (
          <p className="text-sm text-text-muted text-center py-8">Нет расписания</p>
        )}
      </motion.div>
    </div>
  )
}
