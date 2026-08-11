import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../services/api'
import type { MedicationCourse } from '../types'

const statusText: Record<string, string> = { recorded: '已收录', awaiting_prescription: '等待补充处方' }

export default function MedicationCoursesPage() {
  const memberId = Number(useParams().memberId)
  const [items, setItems] = useState<MedicationCourse[]>([])
  const [loading, setLoading] = useState(true)
  useEffect(() => { api.medicationCourses(memberId).then(rows => setItems(rows as MedicationCourse[])).finally(() => setLoading(false)) }, [memberId])

  return <section><p className="eyebrow">中药疗程</p><h1>每一副药和换方经过</h1><p>处方原图、医生、时间和每日反应分别保存；药名看不清时以原图和医生确认为准。</p><div className="action-row"><Link className="secondary link-button" to={`/documents/${memberId}`}>查看处方原图</Link><Link className="secondary link-button" to={`/members/${memberId}`}>查看健康时间线</Link></div>{loading && <p>正在读取中药疗程…</p>}{!loading && items.length === 0 && <p className="empty-state">还没有中药疗程记录。</p>}<div className="course-list">{items.map(item => <article className="card course-card" key={item.id}><div><span className="course-number">第{item.course_number}副</span><span className={`course-status ${item.status === 'awaiting_prescription' ? 'pending' : ''}`}>{statusText[item.status] || item.status}</span></div><h2>{item.formula_relation || '处方已收录'}</h2><dl><dt>处方日期</dt><dd>{item.prescription_date || '待补充'}</dd><dt>主诊医生</dt><dd>{item.doctor || '待确认'}</dd><dt>医院科室</dt><dd>{[item.hospital, item.department].filter(Boolean).join(' · ') || '待补充'}</dd><dt>服法</dt><dd>{item.dosage_instructions || '待医生或处方确认'}</dd></dl></article>)}</div></section>
}
