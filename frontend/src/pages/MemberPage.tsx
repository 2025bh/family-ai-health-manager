import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../services/api'
import type { TimelineItem } from '../types'

const KIND_LABELS: Record<string, string> = { health_log: '健康日志', measurement: '测量', medical_visit: '就医', care_task: '任务', document: '检查资料', medication_course: '中药' }
const KIND_ORDER = ['all', 'health_log', 'measurement', 'medical_visit', 'care_task', 'document', 'medication_course']
const SOURCE_LABELS: Record<string, string> = { user_reported: '本人记录', uploaded_document: '上传资料', system: '系统', manual: '手工录入' }

function withinDays(time: string, days: number | null): boolean {
  if (!days) return true
  const diff = Date.now() - new Date(time).getTime()
  return diff >= 0 && diff <= days * 24 * 60 * 60 * 1000
}

export default function MemberPage() {
  const id = Number(useParams().id)
  const [info, setInfo] = useState<Record<string, any>>()
  const [timeline, setTimeline] = useState<TimelineItem[]>([])
  const [kindFilter, setKindFilter] = useState('all')
  const [daysFilter, setDaysFilter] = useState<number | null>(null)
  const [onlyAbnormal, setOnlyAbnormal] = useState(false)
  const [query, setQuery] = useState('')
  const [visibleCount, setVisibleCount] = useState(25)
  useEffect(() => { api.member(id).then(setInfo); api.timeline(id).then(setTimeline) }, [id])
  useEffect(() => { setVisibleCount(25) }, [kindFilter, daysFilter, onlyAbnormal, query])
  const filtered = useMemo(() => timeline.filter(item =>
    (kindFilter === 'all' || item.kind === kindFilter) &&
    withinDays(item.time, daysFilter) &&
    (!onlyAbnormal || item.safety_attention) &&
    (!query.trim() || item.title.toLowerCase().includes(query.trim().toLowerCase()))
  ), [timeline, kindFilter, daysFilter, onlyAbnormal, query])
  const visible = filtered.slice(0, visibleCount)
  const grouped = visible.reduce<Record<string, TimelineItem[]>>((result, item) => {
    const date = new Date(item.time).toLocaleDateString('zh-CN')
    ;(result[date] ||= []).push(item)
    return result
  }, {})
  if (!info) return <p>正在读取健康档案…</p>
  const profile = info.profile || {}
  const detail = profile.structured || {}
  return <section><p className="eyebrow">个人健康档案 {profile.profile_version || ''}</p><h1>{info.member?.name}的健康主页</h1><div className="action-row"><Link className="primary link-button" to={`/daily-log/${id}`}>开始记录</Link><Link className="secondary link-button" to={`/doctor-mode/${id}`}>我要去看医生</Link></div><div className="summary-grid"><article className="card"><h3>已知健康问题</h3><p>{profile.known_conditions || '未知'}</p></article><article className="card"><h3>当前长期用药</h3><p>{profile.medications || '未知'}</p></article><article className="card"><h3>近30天记录</h3><strong>{info.recent_logs?.length || 0} 条</strong></article></div><div className="summary-grid"><article className="card"><h3>基础信息</h3><p>{info.member?.gender || '性别待补充'} · {detail.age_text || '年龄待补充'}</p><p>{profile.height ? `${profile.height} cm` : '身高待补充'} · {profile.weight ? `${profile.weight} kg` : '体重待补充'}</p><p>{profile.occupation || '职业待补充'}</p></article><article className="card"><h3>当前主要表现</h3><p>{(detail.current_symptoms || []).join('、') || '待补充'}</p></article><article className="card"><h3>管理重点</h3><p>{(detail.care_priorities || []).join('、') || '待补充'}</p></article></div><h2>健康时间线</h2><div className="timeline-tools" role="group" aria-label="时间线筛选"><label className="timeline-search">搜索记录<input value={query} onChange={event => setQuery(event.target.value)} placeholder="例如：失眠、腹泻、遗精" /></label><div className="filter-row">{KIND_ORDER.map(kind => <button key={kind} className={`chip ${kindFilter === kind ? 'chip-on' : ''}`} onClick={() => setKindFilter(kind)}>{kind === 'all' ? '全部' : (KIND_LABELS[kind] || kind)}</button>)}</div><div className="filter-row">{[[null, '全部时间'], [7, '最近7天'], [30, '最近30天']].map(([days, label]) => <button key={String(days)} className={`chip ${daysFilter === days ? 'chip-on' : ''}`} onClick={() => setDaysFilter(days as number | null)}>{label}</button>)}</div><label className="toggle-label"><input type="checkbox" checked={onlyAbnormal} onChange={e => setOnlyAbnormal(e.target.checked)} /> 只看需要提醒医生的异常</label></div><p className="hint">共 {filtered.length} 条，当前显示 {visible.length} 条</p><div className="timeline-groups">{Object.entries(grouped).map(([date, items], index) => <details className="timeline-day" key={date} open={index < 2 ? true : undefined}><summary>{date}<span>{items.length} 条</span></summary><div className="timeline">{items.map(item => <article key={`${item.kind}-${item.id}`} className={`tl-${item.kind}`}><time>{new Date(item.time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}</time><span className="tl-kind">{KIND_LABELS[item.kind] || item.kind}</span>{item.safety_attention && <strong className="safety-warning">⚠ 需要尽快向医生说明</strong>}<p>{item.title}</p><small>来源：{SOURCE_LABELS[item.source] || item.source}</small></article>)}</div></details>)}</div>{visible.length < filtered.length && <button className="secondary load-more" onClick={() => setVisibleCount(count => count + 25)}>再显示 25 条</button>}{filtered.length === 0 && <p className="empty-state">当前筛选下没有记录。</p>}</section>
}
