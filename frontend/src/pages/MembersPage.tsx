import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import type { Member } from '../types'

export default function MembersPage() {
  const [members, setMembers] = useState<Member[]>([])
  useEffect(() => { api.members().then(setMembers) }, [])
  return <section><h1>家庭成员</h1><p className="muted">演示家庭全部为虚构数据。</p><div className="card-grid">{members.map(m => <Link className="card" to={`/members/${m.id}`} key={m.id}><div className="avatar large">{m.name.slice(0, 1)}</div><h2>{m.name}</h2><p>{m.relationship || '家庭成员'}</p></Link>)}</div></section>
}

