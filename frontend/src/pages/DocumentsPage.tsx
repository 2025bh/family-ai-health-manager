import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, documentFileUrl, documentThumbUrl } from '../services/api'
import type { HealthDocumentItem } from '../types'

const TYPE_LABELS: Record<string, string> = { lab_report: '化验单', prescription: '处方', imaging: '影像', doctor_note: '医嘱单', other: '其他' }
const TYPE_COLORS: Record<string, string> = { lab_report: 'lab', prescription: 'rx', imaging: 'img', doctor_note: 'note', other: 'other' }

function titleOf(name: string): string {
  const cleaned = name.replace(/\.(pdf|png|jpe?g|webp)$/i, '')
  return cleaned || name
}

function displayTitle(item: HealthDocumentItem): string {
  return item.display_name || titleOf(item.file_name)
}

function formatDate(value?: string): string {
  if (!value) return '日期未填'
  return value.slice(0, 10)
}

export default function DocumentsPage() {
  const memberId = Number(useParams().memberId)
  const [items, setItems] = useState<HealthDocumentItem[]>([])
  const [typeFilter, setTypeFilter] = useState('all')
  const [message, setMessage] = useState('')
  const [preview, setPreview] = useState<HealthDocumentItem | null>(null)

  const load = () => api.documents(memberId).then(setItems)
  useEffect(() => { void load() }, [memberId])

  const filtered = useMemo(() => (typeFilter === 'all' ? items : items.filter(x => x.document_type === typeFilter)), [items, typeFilter])

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    form.set('member_id', String(memberId))
    const result = await api.uploadDocument(form)
    setMessage(String(result.privacy))
    e.currentTarget.reset()
    load()
  }

  function open(item: HealthDocumentItem) {
    if (item.is_image) setPreview(item)
    else window.open(documentFileUrl(item.id), '_blank')
  }

  return <section>
    <p className="eyebrow">检查资料</p>
    <h1>检查资料</h1>
    <p className="muted">原始 PDF/图片只保存在本机，飞书只同步摘要和索引。列表显示缩略图，点击可查看原图。</p>
    <form className="card form-stack" onSubmit={submit}>
      <h2>上传新资料</h2>
      <label>选择文件（PDF 或图片）<input type="file" name="file" accept=".pdf,.png,.jpg,.jpeg,.webp" required /></label>
      <label>资料类型<select name="document_type" defaultValue="lab_report">{Object.entries(TYPE_LABELS).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
      <label>检查日期<input type="date" name="document_date" /></label>
      <label>家属摘要（可选）<textarea name="manual_summary" rows={2} placeholder="例如：2026年8月体检，血常规和肝功能正常。" /></label>
      <button className="primary">保存资料</button>
    </form>
    {message && <p className="success">{message}</p>}
    <div className="filter-row" role="group" aria-label="按类型筛选">
      {[['all', '全部'], ...Object.entries(TYPE_LABELS)].map(([key, label]) => <button key={key} className={`chip ${typeFilter === key ? 'chip-on' : ''}`} onClick={() => setTypeFilter(key)}>{label}</button>)}
    </div>
    {filtered.length === 0 && <p className="empty-state">{items.length === 0 ? '还没有检查资料，先上传第一份吧。' : '这个分类下还没有资料。'}</p>}
    <div className="doc-grid">
      {filtered.map(item => (
        <button type="button" className="doc-card" key={item.id} onClick={() => open(item)} aria-label={`查看${displayTitle(item)}`}>
          <span className={`doc-type doc-${TYPE_COLORS[item.document_type] || 'other'}`}>{TYPE_LABELS[item.document_type] || '其他'}</span>
          {item.is_image && item.thumbnail_url
            ? <img className="doc-thumb" src={documentThumbUrl(item.id)} alt={displayTitle(item)} loading="lazy" />
            : <span className="doc-file-icon">PDF</span>}
          <span className="doc-name">{displayTitle(item)}</span>
          <time>{formatDate(item.document_date)}</time>
          {item.ai_summary && <span className="doc-summary">{item.ai_summary}</span>}
        </button>
      ))}
    </div>
    {preview && (
      <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={displayTitle(preview)} onClick={() => setPreview(null)}>
        <div className="modal" onClick={e => e.stopPropagation()}>
          <div className="modal-head"><strong>{displayTitle(preview)}</strong><button className="icon-btn" onClick={() => setPreview(null)} aria-label="关闭">×</button></div>
          <img className="modal-img" src={documentFileUrl(preview.id)} alt={displayTitle(preview)} />
          <p className="modal-hint">点击图片可滚动查看细节；也可<a href={documentFileUrl(preview.id)} target="_blank" rel="noreferrer">在新标签打开原图</a>。</p>
        </div>
      </div>
    )}
  </section>
}
