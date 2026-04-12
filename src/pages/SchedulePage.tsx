import { useState, useEffect, useRef, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { slideUp, spring } from '../lib/motion'
import { Search, X, Clock, MapPin, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'
import { useSchedule, useGroupSearch } from '../hooks/useSchedule'
import type { ScheduleEvent, SearchItem } from '../lib/types'

function formatTime(iso: string) {
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

function groupEventsByDay(events: ScheduleEvent[]) {
  const days = new Map<string, ScheduleEvent[]>()
  for (const ev of events) {
    const dateKey = ev.start.slice(0, 10)
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
        <div className="flex items-center gap-1 text-xs text-brand shrink-0">
          <Clock size={12} />
          {formatTime(event.start)}
          {event.end && ` – ${formatTime(event.end)}`}
        </div>
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
  const [query, setQuery] = useState('')
  const [selectedGroup, setSelectedGroup] = useState<SearchItem | null>(null)
  const [focusDate, setFocusDate] = useState(() => new Date())
  const { schedule, loading, error, fetchSchedule } = useSchedule()
  const { groups, loading: searchLoading, search } = useGroupSearch()
  const [showSearch, setShowSearch] = useState(true)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined)

  useEffect(() => {
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => search(query), 300)
    return () => clearTimeout(debounceRef.current)
  }, [query, search])

  const handleSelectGroup = (group: SearchItem) => {
    setSelectedGroup(group)
    setShowSearch(false)
    setQuery('')
    const params: Record<string, string> = { type: 'group' }
    if (group.uid) params.uid = group.uid
    else params.group_name = group.name
    fetchSchedule(params)
  }

  const eventsByDay = useMemo(
    () => (schedule ? groupEventsByDay(schedule.events) : new Map<string, ScheduleEvent[]>()),
    [schedule],
  )

  const focusKey = focusDate.toISOString().slice(0, 10)
  const dayEvents: ScheduleEvent[] = eventsByDay.get(focusKey) || []
  const allDays = [...eventsByDay.keys()].sort()

  const shiftDay = (dir: number) => {
    const idx = allDays.indexOf(focusKey)
    if (idx === -1) {
      const next = new Date(focusDate)
      next.setDate(next.getDate() + dir)
      setFocusDate(next)
    } else {
      const nextIdx = Math.max(0, Math.min(allDays.length - 1, idx + dir))
      setFocusDate(new Date(allDays[nextIdx] + 'T00:00:00'))
    }
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <motion.div variants={slideUp} initial="enter" animate="active" className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-text-primary">Расписание</h1>
          {selectedGroup && (
            <button
              onClick={() => {
                setSelectedGroup(null)
                setShowSearch(true)
              }}
              className="text-xs text-brand"
            >
              Сменить группу
            </button>
          )}
        </div>

        {/* Search */}
        {showSearch && (
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              placeholder="Поиск группы..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-9 pr-9 py-3 bg-surface-2 border border-border rounded-xl text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-border-active transition-colors"
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted"
              >
                <X size={16} />
              </button>
            )}
          </div>
        )}

        {/* Search results */}
        {showSearch && query.length >= 2 && (
          <div className="space-y-1">
            {searchLoading ? (
              <div className="flex justify-center py-4">
                <Loader2 size={20} className="animate-spin text-text-muted" />
              </div>
            ) : groups.length > 0 ? (
              groups.map((g) => (
                <button
                  key={g.uid || g.name}
                  onClick={() => handleSelectGroup(g)}
                  className="w-full text-left px-4 py-3 bg-surface-2 rounded-xl text-sm text-text-primary hover:border-border-active border border-border transition-colors"
                >
                  {g.name}
                </button>
              ))
            ) : (
              <p className="text-sm text-text-muted text-center py-4">Ничего не найдено</p>
            )}
          </div>
        )}

        {/* Selected group indicator */}
        {selectedGroup && !showSearch && (
          <div className="text-sm text-text-secondary">
            Группа: <span className="text-text-primary font-medium">{selectedGroup.name}</span>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex justify-center py-12">
            <Loader2 size={24} className="animate-spin text-brand" />
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-danger/10 text-danger text-sm rounded-xl p-4 text-center">{error}</div>
        )}

        {/* Day navigation */}
        {schedule && !loading && allDays.length > 0 && (
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

            {/* Day dots */}
            <div className="flex justify-center gap-1.5">
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

            {/* Events */}
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

        {/* Empty state */}
        {!schedule && !loading && !showSearch && (
          <p className="text-sm text-text-muted text-center py-8">Выберите группу для просмотра расписания</p>
        )}
      </motion.div>
    </div>
  )
}
