import { useState, useCallback } from 'react'
import { api } from '../lib/api'
import type { ScheduleResponse, SearchItem } from '../lib/types'

export function useSchedule() {
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSchedule = useCallback(
    async (params: Record<string, string>) => {
      setLoading(true)
      setError(null)
      try {
        const query = new URLSearchParams(params).toString()
        const res = await api<ScheduleResponse>(`/api/schedule?${query}`)
        if (res.success) {
          setSchedule(res)
        } else {
          setError(res.message || 'Ошибка загрузки расписания')
        }
      } catch {
        setError('Не удалось загрузить расписание')
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  return { schedule, loading, error, fetchSchedule }
}

export function useGroupSearch() {
  const [groups, setGroups] = useState<SearchItem[]>([])
  const [loading, setLoading] = useState(false)

  const search = useCallback(async (q: string) => {
    if (q.length < 2) {
      setGroups([])
      return
    }
    setLoading(true)
    try {
      const res = await api<{ success: boolean; groups: SearchItem[] }>(
        `/api/groups/search?q=${encodeURIComponent(q)}`,
      )
      setGroups(res.groups || [])
    } catch {
      setGroups([])
    } finally {
      setLoading(false)
    }
  }, [])

  return { groups, loading, search }
}
