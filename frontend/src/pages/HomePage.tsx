import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import VoicePanel from '../components/VoicePanel'
import TodayHealthGuard from '../components/TodayHealthGuard'
import { api } from '../services/api'
import type { HealthAnalysis, HealthGuardSettings, Member, WeeklySummary } from '../types'

export default function HomePage() {
  const [members, setMembers] = useState<Member[]>([])
  const [selected, setSelected] = useState<number>(() => Number(localStorage.getItem('familycare-selected-member')) || 1)
  const [tasks, setTasks] = useState<Array<Record<string, unknown>>>([])
  const [weekly, setWeekly] = useState<WeeklySummary>()
  const [guard, setGuard] = useState<HealthAnalysis>()
  const [guardSettings, setGuardSettings] = useState<HealthGuardSettings>()
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState<Record<string, boolean>>({ members: true, tasks: true, weekly: true, guard: true })

  useEffect(() => {
    api.members().then(rows => {
      setMembers(rows)
      setSelected(current => rows.some(x => x.id === current) ? current : (rows[0]?.id || 1))
    }).catch(() => setErrors(current => ({ ...current, members: '家庭成员读取失败，请稍后重试。' }))).finally(() => setLoading(current => ({ ...current, members: false })))
  }, [])

  function loadMemberData(id: number) {
    setTasks([])
    setWeekly(undefined)
    setGuard(undefined)
    setGuardSettings(undefined)
    setLoading(current => ({ ...current, tasks: true, weekly: true, guard: true }))
    setErrors(current => ({ ...current, tasks: '', weekly: '', guard: '' }))
    api.tasks(id).then(setTasks).catch(() => setErrors(current => ({ ...current, tasks: '今日提醒读取失败，暂时无法判断是否有待办。' }))).finally(() => setLoading(current => ({ ...current, tasks: false })))
    api.weeklySummary(id).then(setWeekly).catch(() => setErrors(current => ({ ...current, weekly: '最近7天摘要读取失败。' }))).finally(() => setLoading(current => ({ ...current, weekly: false })))
    Promise.all([api.healthGuardAnalysis(id, 7), api.healthGuardSettings(id)]).then(([analysis, settings]) => { setGuard(analysis); setGuardSettings(settings) }).catch(() => setErrors(current => ({ ...current, guard: '健康守护结果读取失败，不能据此判断当前风险。' }))).finally(() => setLoading(current => ({ ...current, guard: false })))
  }

  useEffect(() => { loadMemberData(selected) }, [selected])
  function selectMember(id: number) {
    setSelected(id)
    localStorage.setItem('familycare-selected-member', String(id))
    window.dispatchEvent(new CustomEvent('familycare-member-change', { detail: id }))
  }
  const activeCategories = weekly?.categories.filter(x => x.items.length > 0) || []
  const pendingTasks = tasks.filter(x => x.status === 'pending')
  const activeMember = members.find(member => member.id === selected)
  return <>
    <section className="today-header"><div><p className="eyebrow">今日健康工作台</p><h1>{activeMember?.preferred_name || activeMember?.name || '家人'}，今天感觉怎么样？</h1><p>先完成今天的记录，再查看真正发生变化的内容。</p></div><Link className="primary today-record" to={`/daily-log/${selected}`}>记录今天</Link></section>
    <section className="member-switch"><div className="section-head"><h2>当前成员</h2><Link to="/members">管理家庭成员</Link></div>{errors.members && <div className="inline-state state-error"><span>{errors.members}</span><button onClick={() => window.location.reload()}>重新加载</button></div>}<div className="member-grid">{members.map(m => <button className={`member-chip ${selected === m.id ? 'selected' : ''}`} aria-pressed={selected === m.id} onClick={() => selectMember(m.id)} key={m.id}><span className="avatar">{m.name.slice(0, 1)}</span>{m.name}</button>)}</div></section>
    <div className="today-grid"><section className="attention"><div className="section-head"><h2>今天要做</h2><Link to={`/tasks/${selected}`}>全部任务</Link></div>{loading.tasks && <p className="muted">正在读取今日提醒…</p>}{errors.tasks && <div className="inline-state state-error"><span>{errors.tasks}</span><button onClick={() => loadMemberData(selected)}>重试</button></div>}{!loading.tasks && !errors.tasks && pendingTasks.slice(0, 3).map(x => <p key={String(x.id)}>○ {String(x.title)}</p>)}{!loading.tasks && !errors.tasks && pendingTasks.length === 0 && <p className="state-ok">今天没有未完成提醒，可以正常记录身体变化。</p>}</section><section className="next-actions"><h2>快捷入口</h2><div><Link to={`/doctor-mode/${selected}`}>准备复诊</Link><Link to={`/medication-courses/${selected}`}>查看中药疗程</Link><Link to={`/documents/${selected}`}>检查资料</Link></div></section></div>
    <TodayHealthGuard memberId={selected} analysis={guard} settings={guardSettings} loading={loading.guard} error={errors.guard} onRetry={() => loadMemberData(selected)} />
    <section className="weekly-summary">
      <div className="section-head"><h2>最近7天健康摘要</h2><span className="hint">{weekly ? `${weekly.start_date} 至 ${weekly.end_date} · ${weekly.log_count} 条记录` : ''}</span></div>
      {loading.weekly && <p className="empty-state">正在读取最近7天摘要…</p>}{errors.weekly && <div className="inline-state state-error"><span>{errors.weekly}</span><button onClick={() => loadMemberData(selected)}>重试</button></div>}
      {!loading.weekly && !errors.weekly && activeCategories.length === 0 && <p className="empty-state">最近7天还没有记录，点“记录今天”告诉小智今天的情况吧。</p>}
      <div className="summary-grid">
        {activeCategories.map(cat => <article className={`card summary-card tone-${cat.key}`} key={cat.key}><h3>{cat.label}</h3>{cat.items.slice(0, 3).map(item => <p key={item.time}><time>{item.date.slice(5)}</time> {item.emergency && <strong className="safety-warning">⚠</strong>}{item.summary_text || item.raw_text}</p>)}</article>)}
      </div>
    </section>
    <section className="more-tools"><h2>更多健康工具</h2><div className="core-actions"><Link className="core-action" to={`/members/${selected}`}><strong>健康趋势</strong><span>查看个人档案和长期时间线</span></Link><Link className="core-action doctor" to={`/doctor-mode/${selected}`}><strong>准备看医生</strong><span>整理近期变化并生成就医摘要</span></Link></div></section>
    <details className="home-chat"><summary>直接和小智补充说明</summary><VoicePanel key={selected} memberId={selected} /></details>
  </>
}
