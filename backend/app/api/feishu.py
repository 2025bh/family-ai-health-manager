from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import CareTask, FamilyMember, HealthDocument, HealthLog, Measurement, MedicalVisit
from app.providers.feishu import get_feishu_provider

router = APIRouter(prefix="/feishu", tags=["飞书同步"])


@router.post("/sync")
def sync_feishu(db: Session = Depends(get_db)):
    # 严格不读取 file_path 对应的原文件内容。
    snapshot = {
        "members": [{"id": x.id, "name": x.name, "relationship": x.relationship, "preferred_name": x.preferred_name} for x in db.scalars(select(FamilyMember))],
        "health_logs": [{"id": x.id, "member_id": x.member_id, "type": x.log_type, "raw_text": x.raw_text, "structured_data": x.structured_data, "source": x.source, "possible_emergency": x.possible_emergency, "occurred_at": x.occurred_at.strftime("%Y-%m-%d %H:%M:%S")} for x in db.scalars(select(HealthLog))],
        "measurements": [{"id": x.id, "member_id": x.member_id, "type": x.type, "value": x.value, "value2": x.value2, "unit": x.unit, "measurement_context": x.measurement_context, "raw_text": x.raw_text, "source": x.source, "measured_at": x.measured_at.strftime("%Y-%m-%d %H:%M:%S")} for x in db.scalars(select(Measurement))],
        "visits": [{"id": x.id, "member_id": x.member_id, "status": x.status, "chief_complaint": x.chief_complaint, "symptom_summary": x.symptom_summary, "medical_history_snapshot": x.medical_history_snapshot, "medication_snapshot": x.medication_snapshot, "doctor_feedback": x.doctor_feedback, "feedback_source": x.feedback_source, "follow_up_date": x.follow_up_date.strftime("%Y-%m-%d 00:00:00") if x.follow_up_date else None} for x in db.scalars(select(MedicalVisit))],
        "tasks": [{"id": x.id, "member_id": x.member_id, "task_type": x.task_type, "title": x.title, "description": x.description, "scheduled_at": x.scheduled_at.strftime("%Y-%m-%d %H:%M:%S") if x.scheduled_at else None, "recurrence": x.recurrence, "source": x.source, "status": x.status} for x in db.scalars(select(CareTask))],
        "documents": [{"id": x.id, "member_id": x.member_id, "document_type": x.document_type, "file_name": x.file_name, "document_date": x.document_date.strftime("%Y-%m-%d 00:00:00") if x.document_date else None, "summary": x.ai_summary, "source": x.source} for x in db.scalars(select(HealthDocument))],
    }
    return get_feishu_provider().sync(snapshot)
