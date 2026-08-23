import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../services/api'
import type { HealthAnalysis, HealthAnalysisResult } from '../types'

const riskLabel = { insufficient_data: '数据暂不足', green: '继续观察', yellow: '值得关注', red: '建议及时处理/就医' }
const trendLabel = { improved: '改善', stable: '基本稳定', worsened: '变差', unknown: '暂无法判断' }
const actionLabel: Record<string, string> = { continue_monitoring: '继续观察', schedule_medical_review: '建议安排医疗复查', seek_timely_medical_evaluation: '建议及时寻求医疗评估', urgent_escalation: '需要优先处理的紧急升级' }
const categoryLabel: Record<string, string> = { overall: '整体概览', digestive: '胃肠', bowel: '排便', sleep: '睡眠', weight: '体重', mood: '情绪', food: '饮食', exercise: '运动', medication_response: '用药反应', blood_pressure: '血压', blood_glucose: '血糖', temperature: '体温', other_symptoms: '其他身体表现' }
const sourceLabel: Record<string, string> = { health_log: '每日健康记录', measurement: '测量记录', medication_course: '用药疗程', medical_visit: '就诊记录', user_statement: '本人描述', document: '检查资料' }
const confidenceLabel: Record<string, string> = { high: '较明确', medium: '需要结合其他记录', low: '仍需确认' }

function ResultCard({ result }: { result: HealthAnalysisResult }) {
  return <article className={`analysis-card risk-border-${result.risk_level}`}>
    <div className="analysis-head"><div><span className="category-kicker">{categoryLabel[result.category] || result.category}</span><h2>{result.summary}</h2></div><span className={`risk-tag risk-${result.risk_level}`}>{riskLabel[result.risk_level]}</span></div>
    <dl className={`analysis-metrics ${result.category === 'overall' ? 'overall-metrics' : ''}`}>{result.category !== 'overall' && <><div><dt>当前周期</dt><dd>{result.current_period_days_with_records} 天有记录</dd><span className="metric-bar"><i style={{ width: `${Math.min(100, result.current_period_days_with_records * 12)}%` }} /></span></div><div><dt>上一周期</dt><dd>{result.baseline_period_days_with_records} 天有记录</dd><span className="metric-bar baseline"><i style={{ width: `${Math.min(100, result.baseline_period_days_with_records * 12)}%` }} /></span></div></>}<div><dt>趋势</dt><dd>{trendLabel[result.trend]}</dd></div><div><dt>下一步</dt><dd>{actionLabel[result.escalation_action] || result.escalation_action}</dd></div></dl>
    <details className="evidence-details" open={result.category === 'overall' || result.risk_level === 'yellow' || result.risk_level === 'red'}><summary>为什么这样判断？</summary>
      <div className="why-grid"><div><h3>我的数据</h3>{result.evidence.length ? <ol>{result.evidence.map(item => <li key={`${item.source_id}-${item.summary}`}><span>{item.summary}</span><small>{sourceLabel[item.source_type] || '健康资料'} · {confidenceLabel[item.confidence] || '可信度待确认'}</small></li>)}</ol> : <p>当前没有足够的对应记录。</p>}</div>
      <div><h3>仍需确认</h3>{result.uncertainty.length ? <ul>{result.uncertainty.map(item => <li key={item}>{item}</li>)}</ul> : <p>本条暂未记录额外不确定项。</p>}<h3>下一步建议</h3><ul>{result.suggestion.map(item => <li key={item}>{item}</li>)}</ul>{result.rule_ids.length > 0 && <details className="technical-details"><summary>技术详情</summary><p>规则编号：{result.rule_ids.join('、')}</p></details>}</div></div>
    </details>
  </article>
}

export default function HealthGuardPage() {
  const memberId = Number(useParams().memberId)
  const [days, setDays] = useState<7 | 30>(7)
  const [analysis, setAnalysis] = useState<HealthAnalysis>()
  const [error, setError] = useState('')
  function loadAnalysis() {
    setAnalysis(undefined)
    setError('')
    api.healthGuardAnalysis(memberId, days).then(setAnalysis).catch(() => setError('健康分析读取失败，当前页面不能据此判断风险。'))
  }
  useEffect(loadAnalysis, [memberId, days])
  const results = analysis?.results || []
  const overall = results.find(result => result.category === 'overall')
  const important = results.filter(result => result.category !== 'overall' && (result.risk_level === 'red' || result.risk_level === 'yellow' || result.trend === 'worsened'))
  const other = results.filter(result => result.category !== 'overall' && !important.includes(result))
  return <section className="focus-page health-analysis-page"><Link to="/" className="summary-link">← 返回今日工作台</Link><p className="eyebrow">近期记录对比</p><h1>健康趋势观察</h1><p className="muted">比较当前周期与上一周期，只说明记录发生的变化，不作疾病诊断。</p>
    <div className="period-switch" role="group" aria-label="分析周期"><button className={days === 7 ? 'chip chip-on' : 'chip'} onClick={() => setDays(7)}>最近7天</button><button className={days === 30 ? 'chip chip-on' : 'chip'} onClick={() => setDays(30)}>最近30天</button></div>
    {analysis?.current_period && <p className="period-note">当前：{analysis.current_period.start.slice(0, 10)} 至 {analysis.current_period.end.slice(0, 10)}　·　对比上一周期</p>}
    {error && <div className="inline-state state-error"><span>{error}</span><button onClick={loadAnalysis}>重新读取</button></div>}{!analysis && !error && <p className="empty-state">正在生成可解释分析…</p>}
    {overall && <div className="analysis-list overall-analysis"><ResultCard result={overall} /></div>}
    {important.length > 0 && <section className="analysis-section"><div className="section-head"><h2>最近需要关注</h2><span className="hint">{important.length} 项发生变化或值得关注</span></div><div className="analysis-list">{important.map(result => <ResultCard key={result.category} result={result} />)}</div></section>}
    {analysis && important.length === 0 && <p className="state-ok analysis-ok">当前没有发现新增的重点变化，请继续记录。</p>}
    {other.length > 0 && <details className="other-analysis"><summary>查看其他正常或数据不足项目（{other.length}）</summary><div className="analysis-list">{other.map(result => <ResultCard key={result.category} result={result} />)}</div></details>}
    <aside className="safety-note"><strong>安全边界</strong><p>红色提醒由明确的安全规则控制；规则版本和证据来源会保留。系统不会自动诊断、开药、停药、换药或调整剂量。</p></aside>
  </section>
}
