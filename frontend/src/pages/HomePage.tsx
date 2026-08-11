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
  useEffect(() => { api.members().then(rows => { setMembers(rows); setSelected(current => rows.some(x => x.id === current) ? current : (rows[0]?.id || 1)) }) }, [])
  useEffect(() => { api.tasks(selected).then(setTasks).catch(() => setTasks([])) }, [selected])
  useEffect(() => { api.weeklySummary(selected).then(setWeekly).catch(() => setWeekly(undefined)) }, [selected])
  useEffect(() => { api.healthGuardAnalysis(selected, 7).then(setGuard).catch(() => setGuard(undefined)); api.healthGuardSettings(selected).then(setGuardSettings).catch(() => setGuardSettings(undefined)) }, [selected])
  function selectMember(id: number) {
    setSelected(id)
    localStorage.setItem('familycare-selected-member', String(id))
  }
  const activeCategories = weekly?.categories.filter(x => x.items.length > 0) || []
  return <>
    <section className="hero"><p className="eyebrow">家医 · FamilyCare AI V0.2</p><h1>记录每次变化，<br />守护长期趋势。</h1><p>长期记录、趋势观察、风险提醒和就医整理。AI 不替医生诊断。</p></section>
    <section><h2>我的家庭</h2><div className="member-grid">{members.map(m => <button className={`member-chip ${selected === m.id ? 'selected' : ''}`} aria-pressed={selected === m.id} onClick={() => selectMember(m.id)} key={m.id}><span className="avatar">{m.name.slice(0, 1)}</span>{m.name}</button>)}</div></section>
    <section className="attention"><h2>今日需要关注</h2>{tasks.filter(x => x.status === 'pending').slice(0, 3).map(x => <p key={String(x.id)}>○ {String(x.title)}</p>)}{tasks.filter(x => x.status === 'pending').length === 0 && <p>今天暂时没有待办提醒。</p>}</section>
    <TodayHealthGuard memberId={selected} analysis={guard} settings={guardSettings} />
    <section className="weekly-summary">
      <div className="section-head"><h2>最近7天健康摘要</h2><span className="hint">{weekly ? `${weekly.start_date} 至 ${weekly.end_date} · ${weekly.log_count} 条记录` : ''}</span></div>
      {activeCategories.length === 0 && <p className="empty-state">{weekly ? '最近7天还没有记录，点“今天记录”告诉小智今天的情况吧。' : '正在读取最近7天摘要…'}</p>}
      <div className="summary-grid">
        {activeCategories.map(cat => <article className={`card summary-card tone-${cat.key}`} key={cat.key}><h3>{cat.label}</h3>{cat.items.slice(0, 3).map(item => <p key={item.time}><time>{item.date.slice(5)}</time> {item.emergency && <strong className="safety-warning">⚠</strong>}{item.summary_text || item.raw_text}</p>)}</article>)}
      </div>
    </section>
    <section><h2>常用功能</h2><div className="core-actions"><Link className="core-action" to={`/daily-log/${selected}`}><strong>今天记录</strong><span>记录身体、睡眠、饮食和用药反应</span></Link><Link className="core-action" to={`/members/${selected}`}><strong>健康趋势</strong><span>查看个人档案和长期时间线</span></Link><Link className="core-action" to={`/medication-courses/${selected}`}><strong>中药疗程</strong><span>查看每一副药和换方经过</span></Link><Link className="core-action doctor" to={`/doctor-mode/${selected}`}><strong>准备看医生</strong><span>整理近期变化并生成就医摘要</span></Link></div></section>
    <div className="support-actions"><Link to={`/documents/${selected}`}>检查资料</Link><Link to={`/tasks/${selected}`}>健康任务</Link><Link to={`/daily-log/${selected}?mode=phone`}>联系家人</Link></div>
    <VoicePanel key={selected} memberId={selected} />
  </>
}
