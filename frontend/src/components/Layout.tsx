import { Link, Outlet } from 'react-router-dom'

export default function Layout() {
  return <>
    <header className="topbar"><Link to="/" className="brand">家医 <span>小智健康管家</span></Link><nav><Link to="/members">家人</Link><Link to="/settings">设置</Link></nav></header>
    <main className="shell"><Outlet /></main>
    <footer>小智帮助整理与提醒，不替代医生诊断或用药建议。</footer>
  </>
}
