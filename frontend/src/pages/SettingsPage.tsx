import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { Member } from '../types'

export default function SettingsPage() {
  const [result, setResult] = useState('')
  const [members, setMembers] = useState<Member[]>([])
  const [memberId, setMemberId] = useState(() => Number(localStorage.getItem('familycare-selected-member')) || 1)
  const [contacts, setContacts] = useState<Array<Record<string, unknown>>>([])
  const [schedule, setSchedule] = useState<Record<string, any>>()
  useEffect(() => { api.members().then(setMembers) }, [])
  useEffect(() => { api.contacts(memberId).then(setContacts); api.schedule(memberId).then(setSchedule) }, [memberId])
  async function sync() { const value = await api.syncFeishu(); setResult(String(value.message || JSON.stringify(value))) }
  async function saveSchedule() { if (!schedule) return; const value = await api.updateSchedule(memberId, schedule); setSchedule(value); setResult('主动询问时间已保存。') }
  function selectMember(id: number) { setMemberId(id); localStorage.setItem('familycare-selected-member', String(id)) }
  return <section><h1>设置</h1><label className="setting-member">正在设置：<select value={memberId} onChange={e => selectMember(Number(e.target.value))}>{members.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}</select></label><div className="settings-list"><article className="card"><h2>家庭成员</h2><p>{members.map(x => x.name).join('、') || '正在读取…'}</p></article><article className="card"><h2>普通电话联系人</h2>{contacts.map(x => <p key={String(x.id)}>{String(x.relationship)}：{String(x.name)}</p>)}{contacts.length === 0 && <p>尚未设置联系人。</p>}</article><article className="card"><h2>智能整理</h2><p>当前使用本机模拟模式，不会把健康资料发送给外部人工智能服务。</p></article><article className="card"><h2>主动询问</h2><p>每位成员可配置早、中、晚时间，也支持今天跳过和稍后提醒。当前只保存时间，真实设备推送尚未连接。</p>{schedule && <div className="schedule-grid"><label><input type="checkbox" checked={schedule.morning_enabled} onChange={e => setSchedule({ ...schedule, morning_enabled: e.target.checked })} /> 早晨</label><input type="time" value={schedule.morning_time} onChange={e => setSchedule({ ...schedule, morning_time: e.target.value })} /><label><input type="checkbox" checked={schedule.afternoon_enabled} onChange={e => setSchedule({ ...schedule, afternoon_enabled: e.target.checked })} /> 午后</label><input type="time" value={schedule.afternoon_time} onChange={e => setSchedule({ ...schedule, afternoon_time: e.target.value })} /><label><input type="checkbox" checked={schedule.evening_enabled} onChange={e => setSchedule({ ...schedule, evening_enabled: e.target.checked })} /> 晚上</label><input type="time" value={schedule.evening_time} onChange={e => setSchedule({ ...schedule, evening_time: e.target.value })} /><label><input type="checkbox" checked={schedule.skip_today} onChange={e => setSchedule({ ...schedule, skip_today: e.target.checked })} /> 今天别问了</label><button className="secondary" onClick={saveSchedule}>保存时间</button></div>}</article><article className="card"><h2>飞书同步</h2><p>当前是模拟同步，只核对数据范围，不会上传个人健康资料或医疗原文件。</p><button className="secondary" onClick={sync}>检查同步范围</button>{result && <p className="success">{result}</p>}</article><article className="card"><h2>小智设备</h2><p>真实小智语音设备尚未连接；现在可以先使用网页文字版的小智健康管家。</p></article></div></section>
}
