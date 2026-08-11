import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../services/api'

const labels: Record<string, string> = { doctor_context: '就诊医生', chief_complaint: '主要问题', start_time: '开始时间', current_trend: '近期总体趋势', frequency: '持续情况', episode_duration: '每次持续多久', triggers: '明显场景', associated_symptoms: '伴随情况', medication_changes: '近期用药变化', question_for_doctor: '想问医生', recent_period: '本次汇总时段', digestive: '消化与排便', sleep_and_energy: '睡眠与精力', mood: '情绪状态', oral_and_other: '口腔及其他表现', nocturnal_emission: '睡眠中遗精', recent_sensitive_symptoms: '近期敏感症状核对', stool_history: '需告知医生的既往排便', medication_course: '近期用药经过' }

export default function VisitPage() {
  const id = Number(useParams().visitId)
  const [summary, setSummary] = useState<Record<string, any>>()
  const [review, setReview] = useState<Record<string, any>>()
  const [confirming, setConfirming] = useState(false)
  const [editingKey, setEditingKey] = useState('')
  const [editValue, setEditValue] = useState('')
  const [savingEdit, setSavingEdit] = useState(false)
  const [sharedMessage, setSharedMessage] = useState('')
  const [error, setError] = useState('')

  async function load() {
    const s = await api.visit(id)
    setSummary(s)
    if (s.status === 'REVIEWING') {
      setReview(await api.visitReview(id))
    } else {
      setReview(undefined)
    }
  }
  useEffect(() => { void load() }, [id])

  async function confirm() {
    setConfirming(true)
    setError('')
    try {
      await api.confirmVisit(id)
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : '确认失败，请稍后再试')
    } finally {
      setConfirming(false)
    }
  }

  function beginEdit(key: string, value: string) {
    setEditingKey(key)
    setEditValue(value)
  }

  async function saveEdit() {
    if (!editingKey || !editValue.trim()) return
    setSavingEdit(true)
    setError('')
    try {
      setReview(await api.updateVisitReview(id, editingKey, editValue.trim()))
      setEditingKey('')
      setEditValue('')
      setSummary(await api.visit(id))
    } catch (e) {
      setError(e instanceof Error ? e.message : '修改失败，请稍后再试')
    } finally { setSavingEdit(false) }
  }

  async function markShared() {
    try {
      await api.markVisitShared(id)
      setSharedMessage('已标记：这份摘要已经给医生看过。')
      await load()
    } catch (e) { setError(e instanceof Error ? e.message : '标记失败') }
  }

  if (!summary) return <p>正在生成摘要…</p>

  if (summary.status === 'REVIEWING' && review) {
    const weekly = review.weekly || {}
    const activeCategories = (weekly.categories || []).filter((x: any) => x.items?.length > 0)
    return <section className="focus-page">
      <p className="eyebrow">生成前核对</p>
      <h1>先核对，再生成《{summary.title || '就医摘要'}》</h1>
      <p className="muted">以下是系统从近期记录里整理出来的内容。请家属逐项核对，确认没有漏掉近期的变化，再点“确认无误”。</p>
      <div className="card review-block"><h2>这次对话整理</h2><dl className="review-dl">{(review.answers || []).map((a: any) => <div key={a.key}><dt>{a.label}</dt><dd>{editingKey === a.key ? <div className="inline-edit"><textarea value={editValue} onChange={e => setEditValue(e.target.value)} rows={3} aria-label={`修改${a.label}`} /><div className="action-row compact"><button className="primary" disabled={savingEdit} onClick={saveEdit}>{savingEdit ? '保存中…' : '保存修改'}</button><button className="secondary" onClick={() => setEditingKey('')}>取消</button></div></div> : <><span>{a.value}</span><button className="text-button" onClick={() => beginEdit(a.key, a.value)}>修改这一项</button></>}</dd></div>)}</dl></div>
      <div className="card review-block"><h2>近14天原始记录核对</h2>{activeCategories.length === 0 && <p className="muted">近14天没有原始日志记录。</p>}{activeCategories.map((cat: any) => <div className="review-cat" key={cat.key}><h3>{cat.label}</h3>{cat.items.map((item: any) => <p key={item.time}><time>{item.date}</time> {item.emergency && <strong className="safety-warning">⚠</strong>}{item.summary_text || item.raw_text}</p>)}</div>)}</div>
      {(review.recent_sensitive_symptoms || []).length > 0 && <div className="card review-block"><h2>近期敏感症状（已单独列出，避免遗漏）</h2><ul>{(review.recent_sensitive_symptoms as string[]).map((x: string, i: number) => <li key={i}>{x}</li>)}</ul></div>}
      <div className="card review-block"><h2>已有档案</h2><p><strong>已知健康问题：</strong>{review.known_conditions || '未知'}</p><p><strong>长期用药：</strong>{review.medications || '未知/待确认'}</p></div>
      {error && <p className="error">{error}</p>}
      <div className="action-row"><button className="primary" disabled={confirming} onClick={confirm}>{confirming ? '正在生成…' : '确认无误，生成正式摘要'}</button><button className="secondary" onClick={() => window.print()}>打印核对清单</button></div>
      <p className="disclaimer">{review.disclaimer}</p>
    </section>
  }

  const reportEntries = Object.entries(summary.symptom_course || {}).filter(([key]) => !['doctor_context_type', 'doctor_name', 'recent_sensitive_symptoms'].includes(key))
  const alreadyShared = ['VISITED', 'FOLLOW_UP'].includes(String(summary.status))
  return <article className="print-sheet"><div className="no-print action-row"><button className="primary" onClick={() => window.print()}>打印 A4 版</button><button className="secondary" disabled={alreadyShared} onClick={markShared}>{alreadyShared ? '已给医生看过' : '标记已给医生看'}</button></div>{sharedMessage && <p className="success no-print">{sharedMessage}</p>}{error && <p className="error no-print">{error}</p>}<h1>{summary.title || '中医就诊摘要'}</h1><dl><dt>姓名</dt><dd>{summary.name}</dd><dt>年龄</dt><dd>{summary.age_text || summary.age || '未知'}</dd><dt>本次主要问题</dt><dd>{summary.main_problem || '待补充'}</dd></dl><h2>近期身体反馈</h2><ul>{reportEntries.map(([key, value]) => <li key={key}><strong>{labels[key] || key}：</strong>{String(value)}</li>)}</ul><h2>已知健康问题</h2><p>{summary.known_conditions || '未知'}</p><h2>近期用药记录</h2><p>{summary.medications || '未知/待确认'}</p>{summary.recent_reports && <><h2>重要检查资料</h2><p className="pre-line">{summary.recent_reports}</p></>}{(summary.recent_measurements || []).length > 0 && <><h2>检查指标提醒</h2><ul>{summary.recent_measurements.map((x: any, i: number) => <li key={i}>{x.type}: {x.value}{x.value2 ? `/${x.value2}` : ''} {x.unit}{x.note ? `（${x.note}）` : ''}</li>)}</ul></>}<h2>本次请医生确认</h2><p className="pre-line">{summary.questions_for_doctor || '待补充'}</p>{summary.doctor_feedback && <><h2>就医后记录</h2><p>{summary.doctor_feedback}</p><small>来源：{summary.doctor_feedback_source}</small></>}<p className="disclaimer">{summary.disclaimer}</p></article>
}
