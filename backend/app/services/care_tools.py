import json
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import CareTask, HealthLog, Measurement, MedicalVisit
from app.services.context_builder import ContextBuilder
from app.services.doctor_mode import DoctorModeService
from app.services.health_parser import HealthLogParser
from app.services.safety import SafetyService
from app.services.western_prevention import WesternPreventionEngine


class CareTools:
    """Agent 的稳定工具层；无论 Mock 还是真实 LLM 都只通过这些函数改数据。"""

    def create_health_log(self, db: Session, member_id: int, raw_text: str, log_type: str, structured_data: dict, source: str = "user_reported") -> HealthLog:
        risk = SafetyService().check_input(raw_text)
        row = HealthLog(member_id=member_id, log_type=log_type, raw_text=raw_text, structured_data=json.dumps(structured_data, ensure_ascii=False), source=source, possible_emergency=risk.possible_emergency)
        db.add(row)
        db.commit()
        db.refresh(row)
        WesternPreventionEngine().recompute(db, member_id, "health_log_created", row.id)
        return row

    def create_measurement(self, db: Session, member_id: int, raw_text: str, data: dict, source: str = "user_reported") -> Measurement:
        row = Measurement(member_id=member_id, raw_text=raw_text, source=source, **data)
        db.add(row)
        db.commit()
        db.refresh(row)
        WesternPreventionEngine().recompute(db, member_id, "measurement_created", row.id)
        return row

    def start_medical_visit(self, db: Session, member_id: int) -> MedicalVisit:
        return DoctorModeService().start(db, member_id)

    def update_medical_visit(self, db: Session, visit: MedicalVisit, text: str) -> tuple[str, bool]:
        return DoctorModeService().continue_visit(db, visit, text)

    def generate_doctor_summary(self, db: Session, visit: MedicalVisit) -> dict:
        return DoctorModeService().summary(db, visit)

    def record_doctor_feedback(self, db: Session, member_id: int, text: str) -> MedicalVisit:
        return DoctorModeService().record_post_visit(db, member_id, text)

    def create_care_task(self, db: Session, member_id: int, title: str, description: str, source: str = "system") -> CareTask:
        row = CareTask(member_id=member_id, task_type="general", title=title, description=description, source=source)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def get_member_health_context(self, db: Session, member_id: int) -> dict:
        return ContextBuilder().build(db, member_id)

    def get_recent_health_logs(self, db: Session, member_id: int, limit: int = 10) -> list[HealthLog]:
        return list(db.scalars(select(HealthLog).where(HealthLog.member_id == member_id).order_by(desc(HealthLog.occurred_at)).limit(limit)))
