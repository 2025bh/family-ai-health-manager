import json
from datetime import datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import FamilyMember, HealthDocument, HealthLog, HealthProfile, Measurement, MedicationCourse, MedicalVisit


class ContextBuilder:
    """按需读取近 30 天上下文，不把整个数据库塞给模型。"""

    def build(self, db: Session, member_id: int, days: int = 30) -> dict:
        member = db.get(FamilyMember, member_id)
        if not member:
            raise ValueError("家庭成员不存在")
        since = datetime.now() - timedelta(days=days)
        profile = db.scalar(select(HealthProfile).where(HealthProfile.member_id == member_id))
        logs = list(db.scalars(select(HealthLog).where(HealthLog.member_id == member_id, HealthLog.occurred_at >= since).order_by(desc(HealthLog.occurred_at)).limit(30)))
        measurements = list(db.scalars(select(Measurement).where(Measurement.member_id == member_id, Measurement.measured_at >= since).order_by(desc(Measurement.measured_at)).limit(20)))
        visits = list(db.scalars(select(MedicalVisit).where(MedicalVisit.member_id == member_id).order_by(desc(MedicalVisit.created_at)).limit(5)))
        documents = list(db.scalars(select(HealthDocument).where(HealthDocument.member_id == member_id).order_by(desc(HealthDocument.document_date), desc(HealthDocument.created_at)).limit(20)))
        medication_courses = list(db.scalars(select(MedicationCourse).where(MedicationCourse.member_id == member_id).order_by(MedicationCourse.course_number)))
        structured_profile = {}
        if profile and profile.profile_data:
            try:
                structured_profile = json.loads(profile.profile_data)
            except json.JSONDecodeError:
                structured_profile = {"parse_error": "结构化档案暂时无法读取"}
        return {
            "member": {"id": member.id, "name": member.name, "preferred_name": member.preferred_name, "gender": member.gender, "birthday": member.birthday.isoformat() if member.birthday else None, "relationship": member.relationship},
            "profile": {
                "profile_version": profile.profile_version if profile else None,
                "occupation": profile.occupation if profile else None,
                "known_conditions": profile.known_conditions if profile else None,
                "medications": profile.medications if profile else None,
                "allergies": profile.allergies if profile else None,
                "past_history": profile.past_history if profile else None,
                "family_history": profile.family_history if profile else None,
                "height": profile.height if profile else None,
                "weight": profile.weight if profile else None,
                "smoking_status": profile.smoking_status if profile else None,
                "drinking_status": profile.drinking_status if profile else None,
                "structured": structured_profile,
            },
            "recent_logs": [{"type": x.log_type, "raw_text": x.raw_text, "occurred_at": x.occurred_at.isoformat(), "source": x.source} for x in logs],
            "recent_measurements": [{"type": x.type, "value": x.value, "value2": x.value2, "unit": x.unit, "context": x.measurement_context, "measured_at": x.measured_at.isoformat()} for x in measurements],
            "recent_visits": [{"id": x.id, "status": x.status, "chief_complaint": x.chief_complaint, "created_at": x.created_at.isoformat()} for x in visits],
            "health_documents": [{"id": x.id, "type": x.document_type, "date": x.document_date.isoformat() if x.document_date else None, "summary": x.ai_summary, "source": x.source} for x in documents],
            "medication_courses": [{"id": x.id, "course_number": x.course_number, "prescription_date": x.prescription_date.isoformat() if x.prescription_date else None, "formula_relation": x.formula_relation, "dosage_instructions": x.dosage_instructions, "status": x.status} for x in medication_courses],
        }
