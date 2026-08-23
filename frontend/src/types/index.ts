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

export type RiskLevel = 'insufficient_data' | 'green' | 'yellow' | 'red'
export type HealthEvidence = { source_type: string; source_id: string; recorded_at?: string; original_text?: string; summary: string; confirmed_by_user: boolean; confidence: string }
export type HealthAnalysisResult = {
  id?: number
  category: string
  status: string
  trend: 'improved' | 'stable' | 'worsened' | 'unknown'
  risk_level: RiskLevel
  summary: string
  evidence: HealthEvidence[]
  uncertainty: string[]
  suggestion: string[]
  escalation_action: string
  rule_ids: string[]
  current_period_days_with_records: number
  baseline_period_days_with_records: number
}
export type HealthAnalysis = {
  run_id?: number
  member_id: number
  engine: 'western'
  enabled?: boolean
  period_days?: 7 | 30
  current_period?: { start: string; end: string }
  baseline_period?: { start: string; end: string }
  engine_version?: string
  rule_set_version?: string
  generated_at?: string
  results: HealthAnalysisResult[]
}
export type HealthGuardSettings = {
  member_id: number
  western_prevention_enabled: boolean
  tcm_health_enabled: boolean
  tcm_enabled_at?: string
  tcm_consent_version?: string
  tcm_depth: 'basic' | 'deep'
  medical_safety_always_enabled: true
  tcm: { enabled: boolean; depth: string; status: string; message: string; analysis_available: boolean }
}

export type MedicalKnowledgeSource = { publisher: string; title: string; code: string; url: string; local_file?: string }
export type MedicalKnowledgeItem = {
  id: string
  title: string
  category: string
  status: string
  risk_level: string
  enabled_for_analysis: boolean
  tags: string[]
  standard_answer: string
  review_notes: string
  sources: MedicalKnowledgeSource[]
}
export type MedicalKnowledge = {
  version: string
  updated_at: string
  disclaimer: string
  total: number
  enabled_for_analysis: number
  pending_review: number
  items: MedicalKnowledgeItem[]
}
