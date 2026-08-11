import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../services/api'
import type { HealthAnalysis, HealthAnalysisResult } from '../types'

const riskLabel = { insufficient_data: '数据暂不足', green: '继续观察', yellow: '值得关注', red: '建议及时处理/就医' }
const trendLabel = { improved: '改善', stable: '基本稳定', worsened: '变差', unknown: '暂无法判断' }
const actionLabel: Record<string, string> = { continue_monitoring: '继续观察', schedule_medical_review: '建议安排医疗复查', seek_timely_medical_evaluation: '建议及时寻求医疗评估', urgent_escalation: '需要优先处理的紧急升级' }
const categoryLabel: Record<string, string> = { overall: '整体概览', digestive: '胃肠', bowel: '排便', sleep: '睡眠', weight: '体重', mood: '情绪', food: '饮食', exercise: '运动', medication_response: '用药反应', blood_pressure: '血压', blood_glucose: '血糖', temperature: '体温', other_symptoms: '其他身体表现' }

function ResultCard({ result }: { result: HealthAnalysisResult }) {
  return <article className={`analysis-card risk-border-${result.risk_level}`}>
    <div className="analysis-head"><div><span className="category-kicker">{categoryLabel[result.category] || result.category}</span><h2>{result.summary}</h2></div><span className={`risk-tag risk-${result.risk_level}`}>{riskLabel[result.risk_level]}</span></div>
    <dl className="analysis-metrics"><div><dt>当前周期</dt><dd>{result.current_period_days_with_records} 天有相关记录</dd></div><div><dt>上一周期</dt><dd>{result.baseline_period_days_with_records} 天有相关记录</dd></div><div><dt>趋势</dt><dd>{trendLabel[result.trend]}</dd></div><div><dt>下一步</dt><dd>{actionLabel[result.escalation_action] || result.escalation_action}</dd></div></dl>
    <details className="evidence-details" open={result.category === 'overall' || result.risk_level === 'yellow' || result.risk_level === 'red'}><summary>为什么这样判断？</summary>
      <div className="why-grid"><div><h3>我的数据</h3>{result.evidence.length ? <ol>{result.evidence.map(item => <li key={`${item.source_id}-${item.summary}`}><span>{item.summary}</span><small>{item.source_type} · 可信度 {item.confidence}</small></li>)}</ol> : <p>当前没有足够的对应记录。</p>}</div>
      <div><h3>系统不确定的地方</h3>{result.uncertainty.length ? <ul>{result.uncertainty.map(item => <li key={item}>{item}</li>)}</ul> : <p>本条暂未记录额外不确定项。</p>}<h3>下一步建议</h3><ul>{result.suggestion.map(item => <li key={item}>{item}</li>)}</ul>{result.rule_ids.length > 0 && <><h3>触发规则</h3><p>{result.rule_ids.join('、')}</p></>}</div></div>
    </details>
  </article>
}

export default function HealthGuardPage() {
  const memberId = Number(useParams().memberId)
  const [days, setDays] = useState<7 | 30>(7)
  const [analysis, setAnalysis] = useState<HealthAnalysis>()
  const [error, setError] = useState('')
  useEffect(() => { setAnalysis(undefined); api.healthGuardAnalysis(memberId, days).then(setAnalysis).catch(err => setError(String(err))) }, [memberId, days])
  const results = analysis?.results || []
  return <section className="focus-page health-analysis-page"><Link to="/" className="summary-link">← 返回首页</Link><p className="eyebrow">Western Prevention Engine</p><h1>现代医学健康守护</h1><p className="muted">比较当前周期与上一周期，只说明记录发生的变化，不作疾病诊断。</p>
    <div className="period-switch" role="group" aria-label="分析周期"><button className={days === 7 ? 'chip chip-on' : 'chip'} onClick={() => setDays(7)}>最近7天</button><button className={days === 30 ? 'chip chip-on' : 'chip'} onClick={() => setDays(30)}>最近30天</button></div>
    {analysis?.current_period && <p className="period-note">当前：{analysis.current_period.start.slice(0, 10)} 至 {analysis.current_period.end.slice(0, 10)}　·　对比上一周期</p>}
    {error && <p className="error">{error}</p>}{!analysis && !error && <p className="empty-state">正在生成可解释分析…</p>}
    <div className="analysis-list">{results.map(result => <ResultCard key={result.category} result={result} />)}</div>
    <aside className="safety-note"><strong>安全边界</strong><p>红色提醒由明确的安全规则控制；规则版本和证据来源会保留。系统不会自动诊断、开药、停药、换药或调整剂量。</p></aside>
  </section>
}
