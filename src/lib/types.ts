export interface ScheduleEvent {
  start: string
  end: string | null
  summary: string
  location: string | null
  description: string
}

export interface ScheduleEntity {
  type: 'group' | 'teacher' | 'classroom'
  name: string | null
  uid: string | null
}

export interface ScheduleResponse {
  success: boolean
  message?: string
  type: string
  entity: ScheduleEntity
  group?: string | null
  events: ScheduleEvent[]
}

export interface SearchItem {
  name: string
  uid: string | null
}

export interface Subject {
  name: string
  discipline_id: string | null
  current_control: number
  semester_control: number
  attendance: number
  attendance_max_possible: number | null
  achievements: number
  additional: number
  total: number
}

export interface GradesResponse {
  success: boolean
  message?: string
  subjects: Subject[]
  semester: string
  needs_auth?: boolean
}

export interface AttendanceEntry {
  lesson_start: string
  attend_type: string
}

export interface AttendanceDetailResponse {
  success: boolean
  message?: string
  summary: {
    total: number
    present: number
    excused: number
    absent: number
  }
  entries: AttendanceEntry[]
}

export interface AcsEvent {
  ts: number
  time: string
  enter_zone: string | null
  exit_zone: string | null
  duration_seconds: number | null
  duration: string
}

export interface AcsResponse {
  success: boolean
  message?: string
  date: string
  events: AcsEvent[]
  needs_auth?: boolean
}

export interface MarkResult {
  name: string
  success: boolean
  message: string
  user_id: number
  is_self: boolean
  needs_auth?: boolean
}

export interface AttendanceMarkResponse {
  success: boolean
  message: string
  results: MarkResult[]
  needs_auth?: boolean
}
