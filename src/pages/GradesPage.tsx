import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { slideUp, spring } from '../lib/motion'
import { RefreshCw, Loader2, ChevronDown, ChevronUp, BookOpen } from 'lucide-react'
import { api } from '../lib/api'
import type { Subject, GradesResponse, AttendanceDetailResponse } from '../lib/types'

function scoreColor(total: number) {
  if (total >= 86) return 'text-success'
  if (total >= 70) return 'text-brand-light'
  if (total >= 50) return 'text-warning'
  return 'text-danger'
}

function ScoreBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  return (
    <div className="h-1.5 bg-surface-3 rounded-full overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className={`h-full rounded-full ${color}`}
      />
    </div>
  )
}

function SubjectCard({
  subject,
  expanded,
  onToggle,
}: {
  subject: Subject
  expanded: boolean
  onToggle: () => void
}) {
  const [detail, setDetail] = useState<AttendanceDetailResponse | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  useEffect(() => {
    if (expanded && !detail && subject.discipline_id) {
      setDetailLoading(true)
      api<AttendanceDetailResponse>(
        `/api/attendance/detail?discipline_id=${encodeURIComponent(subject.discipline_id)}`,
      )
        .then((res) => {
          if (res.success) setDetail(res)
        })
        .finally(() => setDetailLoading(false))
    }
  }, [expanded, detail, subject.discipline_id])

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface-2 rounded-xl border border-border overflow-hidden"
    >
      <button onClick={onToggle} className="w-full text-left p-4 space-y-3">
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-sm font-medium text-text-primary leading-snug flex-1">
            {subject.name}
          </h3>
          <div className="flex items-center gap-2 shrink-0">
            <span className={`text-lg font-bold tabular-nums ${scoreColor(subject.total)}`}>
              {subject.total.toFixed(0)}
            </span>
            {expanded ? (
              <ChevronUp size={16} className="text-text-muted" />
            ) : (
              <ChevronDown size={16} className="text-text-muted" />
            )}
          </div>
        </div>

        {/* Score breakdown */}
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div>
            <span className="text-text-muted">ТК</span>
            <span className="ml-1 text-text-secondary">{subject.current_control.toFixed(1)}</span>
          </div>
          <div>
            <span className="text-text-muted">Посещ.</span>
            <span className="ml-1 text-text-secondary">
              {subject.attendance.toFixed(1)}
              {subject.attendance_max_possible != null && (
                <span className="text-text-muted">/{subject.attendance_max_possible}</span>
              )}
            </span>
          </div>
          <div>
            <span className="text-text-muted">СК</span>
            <span className="ml-1 text-text-secondary">{subject.semester_control.toFixed(1)}</span>
          </div>
        </div>

        <ScoreBar
          value={subject.total}
          max={100}
          color={
            subject.total >= 86
              ? 'bg-success'
              : subject.total >= 70
                ? 'bg-brand'
                : subject.total >= 50
                  ? 'bg-warning'
                  : 'bg-danger'
          }
        />
      </button>

      {/* Expanded attendance detail */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 pt-0 border-t border-border">
              {detailLoading ? (
                <div className="flex justify-center py-4">
                  <Loader2 size={16} className="animate-spin text-text-muted" />
                </div>
              ) : detail ? (
                <div className="space-y-3 pt-3">
                  <div className="grid grid-cols-4 gap-2 text-xs text-center">
                    <div>
                      <div className="text-text-muted">Всего</div>
                      <div className="font-medium text-text-primary">{detail.summary.total}</div>
                    </div>
                    <div>
                      <div className="text-text-muted">Был</div>
                      <div className="font-medium text-success">{detail.summary.present}</div>
                    </div>
                    <div>
                      <div className="text-text-muted">Уваж.</div>
                      <div className="font-medium text-warning">{detail.summary.excused}</div>
                    </div>
                    <div>
                      <div className="text-text-muted">Пропуск</div>
                      <div className="font-medium text-danger">{detail.summary.absent}</div>
                    </div>
                  </div>

                  {detail.entries.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {detail.entries.map((e, i) => (
                        <div
                          key={i}
                          title={new Date(e.lesson_start).toLocaleString('ru-RU')}
                          className={`w-5 h-5 rounded text-[9px] flex items-center justify-center font-medium ${
                            e.attend_type === 'present'
                              ? 'bg-success/20 text-success'
                              : e.attend_type === 'excused'
                                ? 'bg-warning/20 text-warning'
                                : 'bg-danger/20 text-danger'
                          }`}
                        >
                          {e.attend_type === 'present' ? '✓' : e.attend_type === 'excused' ? 'У' : '✕'}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-text-muted text-center py-3">
                  {subject.discipline_id ? 'Нет данных' : 'Детализация недоступна'}
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default function GradesPage() {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [semester, setSemester] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null)
  const [needsAuth, setNeedsAuth] = useState(false)

  const fetchGrades = useCallback(async (refresh = false) => {
    setLoading(true)
    setError(null)
    try {
      const url = refresh ? '/api/grades?refresh=1' : '/api/grades'
      const res = await api<GradesResponse>(url)
      if (res.success) {
        setSubjects(res.subjects)
        setSemester(res.semester)
        setNeedsAuth(false)
      } else if (res.needs_auth) {
        setNeedsAuth(true)
      } else {
        setError(res.message || 'Ошибка загрузки')
      }
    } catch {
      setError('Не удалось загрузить оценки')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchGrades()
  }, [fetchGrades])

  const avgTotal = subjects.length > 0
    ? subjects.reduce((s, sub) => s + sub.total, 0) / subjects.length
    : 0

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <motion.div variants={slideUp} initial="enter" animate="active" className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-text-primary">БРС</h1>
            {semester && (
              <p className="text-xs text-text-secondary mt-0.5">{semester}</p>
            )}
          </div>
          <button
            onClick={() => fetchGrades(true)}
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
              Подключите аккаунт МИРЭА в профиле для просмотра оценок
            </p>
          </div>
        )}

        {/* Summary */}
        {subjects.length > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={spring}
            className="bg-surface-2 rounded-xl border border-border p-4 flex items-center justify-between"
          >
            <div>
              <p className="text-xs text-text-muted">Средний балл</p>
              <p className={`text-2xl font-bold tabular-nums ${scoreColor(avgTotal)}`}>
                {avgTotal.toFixed(1)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-text-muted">Дисциплин</p>
              <p className="text-2xl font-bold text-text-primary tabular-nums">
                {subjects.length}
              </p>
            </div>
          </motion.div>
        )}

        {loading && subjects.length === 0 && (
          <div className="flex justify-center py-12">
            <Loader2 size={24} className="animate-spin text-brand" />
          </div>
        )}

        {error && (
          <div className="bg-danger/10 text-danger text-sm rounded-xl p-4 text-center">{error}</div>
        )}

        {/* Subject list */}
        <div className="space-y-3">
          {subjects.map((sub, i) => (
            <SubjectCard
              key={sub.discipline_id || sub.name}
              subject={sub}
              expanded={expandedIdx === i}
              onToggle={() => setExpandedIdx(expandedIdx === i ? null : i)}
            />
          ))}
        </div>
      </motion.div>
    </div>
  )
}
