import { useParams } from 'react-router-dom'
import VoicePanel from '../components/VoicePanel'

export default function DoctorModePage() {
  const memberId = Number(useParams().memberId)
  return <section className="focus-page"><p className="eyebrow">看医生模式</p><h1>我们一次只说一件事。</h1><p>小智健康管家会读取已经知道的档案，不重复盘问。</p><VoicePanel memberId={memberId} initialText="我准备去医院看看。" title="准备看医生" /></section>
}
