import mimetypes
import shutil
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.entities import HealthDocument
from app.providers.document import MockDocumentParser

router = APIRouter(prefix="/documents", tags=["健康资料"])
allowed_suffixes = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
image_suffixes = {".png", ".jpg", ".jpeg", ".webp"}
THUMB_MAX_SIZE = 420


def _is_image(file_path: str | Path) -> bool:
    return Path(file_path).suffix.lower() in image_suffixes


def thumbnail_path_for(file_path: str | Path) -> Path:
    """缩略图按文件名规则放在 data/uploads/thumbs 下，不新增数据库字段。"""
    src = Path(file_path)
    return Path(settings.upload_dir) / "thumbs" / f"{src.stem}.webp"


def ensure_thumbnail(file_path: str | Path) -> Path | None:
    """为图片生成/复用一张 WebP 缩略图；失败时返回 None，不影响原文件。"""
    src = Path(file_path)
    if not _is_image(src) or not src.exists():
        return None
    dst = thumbnail_path_for(src)
    if dst.exists():
        return dst
    try:
        from PIL import Image

        dst.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as im:
            im.thumbnail((THUMB_MAX_SIZE, THUMB_MAX_SIZE))
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGBA")
            else:
                im = im.convert("RGB")
            im.save(dst, "WEBP", quality=82, method=4)
        return dst
    except Exception:
        return None


def _document_view(row: HealthDocument) -> dict:
    is_image = _is_image(row.file_path)
    document_type = _effective_document_type(row)
    return {
        "id": row.id,
        "member_id": row.member_id,
        "document_type": document_type,
        "file_name": row.file_name,
        "display_name": _display_name(row, document_type),
        "document_date": row.document_date.isoformat() if row.document_date else None,
        "ai_summary": row.ai_summary,
        "created_at": row.created_at.isoformat(),
        "is_image": is_image,
        "file_url": f"/api/documents/{row.id}/file",
        "thumbnail_url": f"/api/documents/{row.id}/thumbnail" if is_image else None,
    }


def _effective_document_type(row: HealthDocument) -> str:
    """旧资料未分类时，根据已人工整理的摘要提供稳定分类，不修改或删除原文件。"""
    stored_type = row.document_type or "other"
    if stored_type.startswith("prescription"):
        return "prescription"
    if stored_type.startswith("outpatient") or stored_type in ("doctor_note", "medical_record"):
        return "doctor_note"
    if stored_type.startswith("lab_"):
        return "lab_report"
    if stored_type in ("gastroscopy_report", "colonoscopy_report", "imaging"):
        return "imaging"
    if stored_type != "other":
        return row.document_type
    text = f"{row.file_name} {row.ai_summary or ''}"
    if any(x in text for x in ("处方", "中草药房", "第六副", "第七副", "第八副")):
        return "prescription"
    if any(x in text for x in ("门诊病历", "门诊记录", "医嘱")):
        return "doctor_note"
    if any(x in text for x in ("胃镜", "肠镜", "影像", "内镜")):
        return "imaging"
    if any(x in text for x in ("血常规", "凝血", "呼气试验", "化验", "检验报告")):
        return "lab_report"
    return "other"


def _display_name(row: HealthDocument, document_type: str) -> str:
    date_text = row.document_date.isoformat() if row.document_date else "日期待补充"
    text = row.ai_summary or ""
    course = "第七、八副" if "第七副" in text and "第八副" in text else next((name for name in ("第一副", "第二副", "第三副", "第四副", "第五副", "第六副", "第七副", "第八副", "第九副") if name in text), None)
    if document_type == "prescription":
        return f"{date_text} {course or '中药'}处方"
    if "胃镜" in text:
        return f"{date_text} 胃镜报告"
    if "肠镜" in text:
        return f"{date_text} 肠镜报告"
    if "血常规" in text or "全血细胞" in text:
        return f"{date_text} 血常规报告"
    if "凝血" in text:
        return f"{date_text} 凝血检查报告"
    if "呼气试验" in text:
        return f"{date_text} 幽门螺杆菌呼气试验"
    if document_type == "doctor_note":
        return f"{date_text} 中医胃肠专科门诊病历"
    return Path(row.file_name).stem


@router.get("")
def list_documents(member_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(select(HealthDocument).where(HealthDocument.member_id == member_id).order_by(desc(HealthDocument.created_at)))
    return [_document_view(x) for x in rows]


@router.post("")
def upload_document(member_id: int = Form(...), document_type: str = Form("other"), document_date: date | None = Form(None), manual_summary: str | None = Form(None), file: UploadFile = File(...), db: Session = Depends(get_db)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed_suffixes:
        raise HTTPException(400, "只支持 PDF 或常见图片格式")
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    target = Path(settings.upload_dir) / safe_name
    with target.open("wb") as output:
        shutil.copyfileobj(file.file, output)
    ensure_thumbnail(target)
    parsed = MockDocumentParser().parse(target)
    row = HealthDocument(member_id=member_id, document_type=document_type, file_name=file.filename or safe_name, file_path=str(target), document_date=document_date, raw_extracted_text=parsed["raw_extracted_text"], ai_summary=manual_summary or parsed["ai_summary"], source="uploaded_document")
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "file_name": row.file_name, "ai_summary": row.ai_summary, "privacy": "原文件仅保存在本地；飞书只同步摘要和索引。"}


@router.get("/{doc_id}/file")
def document_file(doc_id: int, db: Session = Depends(get_db)):
    row = db.get(HealthDocument, doc_id)
    if not row:
        raise HTTPException(404, "资料不存在")
    path = Path(row.file_path)
    if not path.exists():
        raise HTTPException(404, "原文件不存在")
    media_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "private, max-age=31536000, immutable"})


@router.get("/{doc_id}/thumbnail")
def document_thumbnail(doc_id: int, db: Session = Depends(get_db)):
    row = db.get(HealthDocument, doc_id)
    if not row:
        raise HTTPException(404, "资料不存在")
    thumb = ensure_thumbnail(row.file_path)
    if not thumb:
        raise HTTPException(404, "该资料没有缩略图")
    return FileResponse(thumb, media_type="image/webp", headers={"Cache-Control": "private, max-age=31536000, immutable"})
