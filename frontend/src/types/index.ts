export type Member = { id: number; name: string; preferred_name?: string; relationship?: string }
export type TimelineItem = { id: number; kind: string; time: string; title: string; source: string; safety_attention?: boolean }
export type VoiceResponse = { session_id: string; intent: string; reply: string; actions: Array<Record<string, unknown>>; data: Record<string, unknown>; possible_emergency: boolean }
export type Message = { role: 'user' | 'assistant'; text: string; emergency?: boolean; healthLogId?: number; originalText?: string; extracted?: string[] }
export type MedicationCourse = { id: number; member_id: number; course_number: number; prescription_date?: string; hospital?: string; department?: string; doctor?: string; formula_relation?: string; dosage_instructions?: string; status: string }
export type HealthDocumentItem = {
  id: number
  member_id: number
  document_type: string
  file_name: string
  display_name?: string
  document_date?: string
  ai_summary?: string
  created_at: string
  is_image: boolean
  file_url: string
  thumbnail_url?: string
}
export type WeeklyCategoryItem = { date: string; time: string; raw_text: string; summary_text?: string; detail: string; emergency: boolean }
export type WeeklyCategory = { key: string; label: string; items: WeeklyCategoryItem[] }
export type WeeklySummary = {
  member_id: number
  member_name: string
  days: number
  start_date: string
  end_date: string
  log_count: number
  measurement_count: number
  categories: WeeklyCategory[]
}
