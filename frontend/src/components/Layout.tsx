import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { api } from '../services/api'
import type { Member } from '../types'

export default function Layout() {
  const [members, setMembers] = useState<Member[]>([])
  const [memberId, setMemberId] = useState(() => Number(localStorage.getItem('familycare-selected-member')) || 1)

  useEffect(() => {
    api.members().then(rows => {
      setMembers(rows)
      setMemberId(current => rows.some(item => item.id === current) ? current : (rows[0]?.id || 1))
    }).catch(() => setMembers([]))
    const syncMember = (event: Event) => setMemberId(Number((event as CustomEvent<number>).detail) || 1)
    window.addEventListener('familycare-member-change', syncMember)
    return () => window.removeEventListener('familycare-member-change', syncMember)
  }, [])

  const member = members.find(item => item.id === memberId)
  return <>
    <header className="topbar">
      <Link to="/" className="brand">家医 <span>小智健康管家</span></Link>
      <nav aria-label="主要导航">
        <NavLink to="/" end>今日</NavLink>
        <NavLink to={`/daily-log/${memberId}`}>记录</NavLink>
        <NavLink to={`/members/${memberId}`}>趋势</NavLink>
        <NavLink to={`/doctor-mode/${memberId}`}>就医</NavLink>
        <NavLink to={`/documents/${memberId}`}>资料</NavLink>
        <NavLink to="/medical-knowledge">医学依据</NavLink>
        <NavLink to="/settings">设置</NavLink>
      </nav>
      <div className="topbar-context"><span>当前成员</span><strong>{member?.preferred_name || member?.name || '读取中'}</strong><Link to="/members">切换</Link></div>
    </header>
    <main className="shell"><Outlet /></main>
    <nav className="mobile-nav" aria-label="手机端主要导航"><NavLink to="/" end>今日</NavLink><NavLink to={`/daily-log/${memberId}`}>记录</NavLink><NavLink to={`/members/${memberId}`}>趋势</NavLink><NavLink to={`/doctor-mode/${memberId}`}>就医</NavLink><NavLink to="/settings">设置</NavLink></nav>
    <footer>小智帮助整理与提醒，不替代医生诊断或用药建议。</footer>
  </>
}
