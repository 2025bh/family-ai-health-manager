from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import CareTask, HealthDocument, HealthLog, Measurement, MedicationCourse, MedicalVisit


def build_timeline(db: Session, member_id: int) -> list[dict]:
    items: list[dict] = []
    for row in db.scalars(select(HealthLog).where(HealthLog.member_id == member_id)):
        items.append({"kind": "health_log", "time": row.occurred_at.isoformat(), "title": row.raw_text, "source": row.source, "id": row.id, "safety_attention": row.possible_emergency})
    for row in db.scalars(select(MedicationCourse).where(MedicationCourse.member_id == member_id)):
        items.append({"kind": "medication_course", "time": (row.prescription_date.isoformat() if row.prescription_date else row.created_at.isoformat()), "title": f"第{row.course_number}副中药：{row.formula_relation or '处方已收录'}", "source": "prescription_document", "id": row.id})
    for row in db.scalars(select(Measurement).where(Measurement.member_id == member_id)):
        value = f"{row.value:g}" + (f"/{row.value2:g}" if row.value2 is not None else "")
        items.append({"kind": "measurement", "time": row.measured_at.isoformat(), "title": f"{row.type} {value} {row.unit}", "source": row.source, "id": row.id})
    for row in db.scalars(select(MedicalVisit).where(MedicalVisit.member_id == member_id)):
        items.append({"kind": "medical_visit", "time": row.created_at.isoformat(), "title": f"就医记录：{row.chief_complaint or row.visit_reason or row.status}", "source": row.feedback_source or "user_reported", "id": row.id})
    for row in db.scalars(select(CareTask).where(CareTask.member_id == member_id)):
        items.append({"kind": "care_task", "time": (row.scheduled_at or row.created_at).isoformat(), "title": f"健康任务：{row.title}", "source": row.source, "id": row.id})
    for row in db.scalars(select(HealthDocument).where(HealthDocument.member_id == member_id)):
        document_time = f"{row.document_date.isoformat()}T00:00:00" if row.document_date else row.created_at.isoformat()
        items.append({"kind": "document", "time": document_time, "title": f"资料：{row.file_name}", "source": row.source, "id": row.id})
    return sorted(items, key=lambda x: x["time"], reverse=True)
