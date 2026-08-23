import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { MedicalKnowledge } from '../types'

export default function MedicalKnowledgePage() {
  const [knowledge, setKnowledge] = useState<MedicalKnowledge>()
  const [error, setError] = useState('')
  useEffect(() => {
    api.medicalKnowledge().then(setKnowledge).catch(() => setError('医学依据读取失败，请稍后重试。'))
  }, [])
  return <section className="focus-page knowledge-page">
    <p className="eyebrow">来源可追溯</p>
    <h1>西医知识与医学依据</h1>
    <p className="muted">这里展示系统已经整理的来源和审核状态。待复核知识不会参与自动诊断、风险分级或用药建议。</p>
    {error && <div className="inline-state state-error"><span>{error}</span><button onClick={() => window.location.reload()}>重新读取</button></div>}
    {!knowledge && !error && <p className="empty-state">正在读取医学依据…</p>}
    {knowledge && <>
      <div className="knowledge-summary">
        <article><strong>{knowledge.total}</strong><span>条知识</span></article>
        <article><strong>{knowledge.pending_review}</strong><span>条待复核</span></article>
        <article><strong>{knowledge.enabled_for_analysis}</strong><span>条已参与分析</span></article>
      </div>
      <p className="safety-note"><strong>当前安全状态：</strong>{knowledge.disclaimer}</p>
      <div className="knowledge-list">{knowledge.items.map(item => <article className="card knowledge-card" key={item.id}>
        <div className="analysis-head"><div><span className="category-kicker">{item.category}</span><h2>{item.title}</h2></div><span className="disabled-label">{item.status}</span></div>
        <p>{item.standard_answer}</p>
        <p className="knowledge-review"><strong>审核提醒：</strong>{item.review_notes}</p>
        <details><summary>查看依据与知识编号</summary><p>知识编号：{item.id}　·　当前不参与自动分析</p><ul>{item.sources.map(source => <li key={`${item.id}-${source.code}`}><a href={source.url} target="_blank" rel="noreferrer">{source.publisher}《{source.title}》</a>（{source.code}）{source.local_file ? ` · 本地已保存：${source.local_file}` : ' · 官方网页来源'}</li>)}</ul></details>
      </article>)}</div>
    </>}
  </section>
}
