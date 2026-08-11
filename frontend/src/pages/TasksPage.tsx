import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../services/api'

export default function TasksPage() {
  const memberId = Number(useParams().memberId)
  const [items, setItems] = useState<Array<Record<string, any>>>([])
  const [busyId, setBusyId] = useState<number>()
  function load() { api.tasks(memberId).then(setItems) }
  useEffect(load, [memberId])
  async function toggleTask(item: Record<string, any>) {
    const taskId = Number(item.id)
    setBusyId(taskId)
    try {
      await api.updateTask(taskId, { status: item.status === 'completed' ? 'pending' : 'completed' })
      load()
    } finally { setBusyId(undefined) }
  }
  const pending = items.filter(item => item.status !== 'completed')
  const completed = items.filter(item => item.status === 'completed')
  const renderTask = (item: Record<string, any>) => <article key={String(item.id)} className={item.status === 'completed' ? 'task-completed' : ''}><h3>{String(item.title)}</h3><p>{String(item.description || '')}</p>{item.scheduled_at && <p className="hint">计划时间：{new Date(String(item.scheduled_at)).toLocaleString('zh-CN')}</p>}<div className="task-footer"><small>来源：{String(item.source || '系统')}</small><button className={item.status === 'completed' ? 'secondary' : 'primary'} disabled={busyId === Number(item.id)} onClick={() => toggleTask(item)}>{busyId === Number(item.id) ? '保存中…' : item.status === 'completed' ? '恢复为待办' : '标记完成'}</button></div></article>
  return <section><p className="eyebrow">持续照护</p><h1>健康任务</h1><p className="hint">把复查、记录和生活调整逐项完成，避免只提醒不闭环。</p><h2>待完成（{pending.length}）</h2>{pending.length ? <div className="timeline task-list">{pending.map(renderTask)}</div> : <p className="empty-state">当前没有待完成任务。</p>}<h2 className="completed-title">已完成（{completed.length}）</h2>{completed.length ? <div className="timeline task-list">{completed.map(renderTask)}</div> : <p className="empty-state">还没有已完成任务。</p>}</section>
}
