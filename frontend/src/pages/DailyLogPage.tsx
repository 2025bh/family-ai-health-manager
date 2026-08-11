import { useParams, useSearchParams } from 'react-router-dom'
import VoicePanel from '../components/VoicePanel'

export default function DailyLogPage() {
  const memberId = Number(useParams().memberId)
  const [params] = useSearchParams()
  const phone = params.get('mode') === 'phone'
  return <section className="focus-page"><h1>{phone ? '联系家人' : '告诉小智今天的情况'}</h1><p>{phone ? '输入“给儿子打电话”，系统会先向你确认。' : '自然地描述就好，原话和整理结果都会保存。'}</p><VoicePanel memberId={memberId} initialText={phone ? '给儿子打电话。' : ''} title={phone ? '联系家人' : '小智健康记录'} /></section>
}
