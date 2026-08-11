import type { HealthDocumentItem, Member, TimelineItem, VoiceResponse, WeeklySummary } from '../types'

export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}/api${path}`, init)
  if (!response.ok) throw new Error((await response.text()) || `请求失败：${response.status}`)
  return response.json() as Promise<T>
}

export const api = {
  members: () => request<Member[]>('/members'),
  member: (id: number) => request<Record<string, unknown>>(`/members/${id}`),
  timeline: (id: number) => request<TimelineItem[]>(`/members/${id}/timeline`),
  weeklySummary: (id: number, days = 7) => request<WeeklySummary>(`/members/${id}/weekly-summary?days=${days}`),
  voice: (memberId: number, text: string, sessionId?: string) => request<VoiceResponse>('/voice/message', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ member_id: memberId, text, session_id: sessionId }) }),
  visit: (id: number) => request<Record<string, unknown>>(`/visits/${id}`),
  visitReview: (id: number) => request<Record<string, any>>(`/visits/${id}/review`),
  confirmVisit: (id: number) => request<Record<string, any>>(`/visits/${id}/confirm`, { method: 'POST' }),
  updateVisitReview: (id: number, key: string, value: string) => request<Record<string, any>>(`/visits/${id}/review`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key, value }) }),
  markVisitShared: (id: number) => request<Record<string, any>>(`/visits/${id}/shared-with-doctor`, { method: 'POST' }),
  visits: (memberId: number) => request<Array<Record<string, unknown>>>(`/visits?member_id=${memberId}`),
  tasks: (memberId: number) => request<Array<Record<string, unknown>>>(`/tasks?member_id=${memberId}`),
  updateTask: (id: number, value: Record<string, unknown>) => request<Record<string, unknown>>(`/tasks/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(value) }),
  schedule: (memberId: number) => request<Record<string, any>>(`/tasks/schedule/${memberId}`),
  updateSchedule: (memberId: number, value: Record<string, unknown>) => request<Record<string, any>>(`/tasks/schedule/${memberId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(value) }),
  contacts: (memberId: number) => request<Array<Record<string, unknown>>>(`/contacts?member_id=${memberId}`),
  documents: (memberId: number) => request<HealthDocumentItem[]>(`/documents?member_id=${memberId}`),
  medicationCourses: (memberId: number) => request<Array<Record<string, any>>>(`/medication-courses?member_id=${memberId}`),
  uploadDocument: (form: FormData) => request<Record<string, unknown>>('/documents', { method: 'POST', body: form }),
  updateHealthLog: (id: number, rawText: string) => request<Record<string, any>>(`/health-logs/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ raw_text: rawText }) }),
  syncFeishu: () => request<Record<string, unknown>>('/feishu/sync', { method: 'POST' }),
}

export function documentFileUrl(id: number): string {
  return `${API_BASE}/api/documents/${id}/file`
}

export function documentThumbUrl(id: number): string {
  return `${API_BASE}/api/documents/${id}/thumbnail`
}
