import { FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import type { Message } from '../types'

export default function VoicePanel({ memberId, initialText = '', title = '跟小智健康管家说话' }: { memberId: number; initialText?: string; title?: string }) {
  const [text, setText] = useState(initialText)
  const [sessionId, setSessionId] = useState<string>()
  const [messages, setMessages] = useState<Message[]>([])
  const [visitId, setVisitId] = useState<number>()
  const [busy, setBusy] = useState(false)
  const [editingLogId, setEditingLogId] = useState<number>()
  const [editText, setEditText] = useState('')
  const [savingCorrection, setSavingCorrection] = useState(false)

  function extractedLabels(data: unknown): string[] {
    if (!data || typeof data !== 'object') return []
    const labels: Record<string, string> = {
      sleep_time: '入睡时间', night_wakings: '夜醒次数', symptom: '症状', duration: '持续时间',
      trigger: '可能诱因', medication: '药物', sexual_health: '睡眠中遗精', description: '原始描述',
    }
    return Object.entries(data as Record<string, unknown>)
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .map(([key, value]) => `${labels[key] || key}：${Array.isArray(value) ? value.join('、') : String(value)}`)
  }

  async function send(event: FormEvent) {
    event.preventDefault()
    if (!text.trim() || busy) return
    const sent = text.trim()
    setMessages(old => [...old, { role: 'user', text: sent }])
    setText('')
    setBusy(true)
    try {
      const result = await api.voice(memberId, sent, sessionId)
      setSessionId(result.session_id)
      const logId = Number(result.data.health_log_id || 0)
      setMessages(old => [...old, {
        role: 'assistant', text: result.reply, emergency: result.possible_emergency,
        healthLogId: logId || undefined, originalText: sent,
        extracted: extractedLabels(result.data.structured_data),
      }])
      const id = Number(result.data.visit_id || 0)
      if (id) setVisitId(id)
    } catch (error) {
      setMessages(old => [...old, { role: 'assistant', text: error instanceof Error ? error.message : '发送失败' }])
    } finally { setBusy(false) }
  }

  async function saveCorrection(logId: number) {
    if (!editText.trim() || savingCorrection) return
    setSavingCorrection(true)
    try {
      const result = await api.updateHealthLog(logId, editText.trim())
      setMessages(old => old.map(message => message.healthLogId === logId ? {
        ...message,
        text: `${message.text}\n\n已按你的修改重新整理。`,
        originalText: editText.trim(),
        extracted: extractedLabels(result.structured_data),
        emergency: Boolean(result.possible_emergency),
      } : message))
      setEditingLogId(undefined)
      setEditText('')
    } catch (error) {
      setMessages(old => [...old, { role: 'assistant', text: error instanceof Error ? error.message : '修改失败，请稍后再试。' }])
    } finally { setSavingCorrection(false) }
  }

  return <section className="voice-card">
    <h2>{title}</h2>
    <div className="chat" aria-live="polite">
      {messages.length === 0 && <p className="hint">可以输入：“最近十来天老是头晕。”</p>}
      {messages.map((m, i) => <div key={i} className={`bubble ${m.role} ${m.emergency ? 'emergency' : ''}`}>
        <span className="pre-line">{m.text}</span>
        {m.role === 'assistant' && m.extracted && m.extracted.length > 0 && <div className="extracted-card"><strong>小智已提取</strong><ul>{m.extracted.map(item => <li key={item}>{item}</li>)}</ul></div>}
        {m.healthLogId && editingLogId !== m.healthLogId && <button type="button" className="text-button" onClick={() => { setEditingLogId(m.healthLogId); setEditText(m.originalText || '') }}>修改刚才记录</button>}
        {m.healthLogId && editingLogId === m.healthLogId && <div className="correction-box"><label htmlFor={`correction-${m.healthLogId}`}>修改原始记录</label><textarea id={`correction-${m.healthLogId}`} rows={3} value={editText} onChange={event => setEditText(event.target.value)} /><div className="action-row compact"><button type="button" className="primary" disabled={savingCorrection} onClick={() => saveCorrection(m.healthLogId!)}>{savingCorrection ? '保存中…' : '保存修改'}</button><button type="button" className="secondary" onClick={() => setEditingLogId(undefined)}>取消</button></div></div>}
      </div>)}
    </div>
    {visitId && <Link className="summary-link" to={`/visits/${visitId}`}>去核对并生成《就医摘要》</Link>}
    <form onSubmit={send} className="speak-form"><label htmlFor="voice-text">输入健康情况</label><textarea id="voice-text" value={text} onChange={e => setText(e.target.value)} placeholder="把今天的身体感觉写在这里……" rows={3} /><button className="primary" disabled={busy}>{busy ? '正在整理…' : '发送'}</button></form>
  </section>
}
