import { Link } from 'react-router-dom'
import type { HealthAnalysis, HealthGuardSettings } from '../types'

const riskLabel = { insufficient_data: '数据暂不足', green: '继续观察', yellow: '值得关注', red: '建议及时处理/就医' }
const riskIcon = { insufficient_data: '○', green: '●', yellow: '●', red: '●' }
const categoryLabel: Record<string, string> = { sleep: '睡眠', digestive: '胃肠', bowel: '排便', weight: '体重' }

export default function TodayHealthGuard({ memberId, analysis, settings, loading, error, onRetry }: { memberId: number; analysis?: HealthAnalysis; settings?: HealthGuardSettings; loading?: boolean; error?: string; onRetry?: () => void }) {
  const overall = analysis?.results.find(item => item.category === 'overall')
  const highlights = analysis?.results.filter(item => categoryLabel[item.category]).slice(0, 4) || []
  const risk = overall?.risk_level || 'insufficient_data'
  return <section className="health-guard-panel">
    <div className="section-head"><div><p className="eyebrow">根据近期记录</p><h2>今日健康守护</h2></div><span className="safety-pill">安全规则已开启</span></div>
    {error && <div className="inline-state state-error"><span>{error}</span>{onRetry && <button onClick={onRetry}>重试</button>}</div>}
    {loading && <p className="muted">正在读取健康守护结果…</p>}
    {!loading && !error && <>
    <div className="guard-grid">
      <article className="guard-card western-card">
        <div className="guard-title"><div><h3>健康趋势观察</h3><span className="enabled-label">默认开启</span></div></div>
        <div className={`risk-banner risk-${risk}`}><span>{riskIcon[risk]}</span><div><small>最近7天</small><strong>{riskLabel[risk]}</strong></div></div>
        <div className="guard-categories">{highlights.map(item => <div key={item.category}><span>{categoryLabel[item.category]}</span><strong className={`text-${item.risk_level}`}>{riskLabel[item.risk_level]}</strong></div>)}</div>
        <Link className="summary-link" to={`/health-guard/${memberId}`}>查看变化和依据 →</Link>
      </article>
      <article className="guard-card tcm-card">
        <div className="guard-title"><div><h3>中医观察</h3><span className={settings?.tcm_health_enabled ? 'enabled-label' : 'disabled-label'}>{settings?.tcm_health_enabled ? '已开启基础观察' : '未开启'}</span></div></div>
        <p>{settings?.tcm_health_enabled ? '当前仅提供基础观察骨架，完整中医辨证分析尚未实现。' : '由你主动选择后，才会增加中医视角的长期健康观察。'}</p>
        <Link className="summary-link" to="/settings">{settings?.tcm_health_enabled ? '查看中医设置' : '开启中医健康守护'} →</Link>
      </article>
    </div>
    <p className="guard-disclaimer">这里只展示记录、趋势和规则提醒，不提供疾病诊断，也不会调整药物或处方。</p>
    </>}
  </section>
}
