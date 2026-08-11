from sqlalchemy import select

from app.models.entities import CareTask
from app.services.doctor_mode import DoctorModeService


def test_post_visit_records_source_and_creates_follow_up(db):
    service = DoctorModeService()
    visit = service.start(db, 4)
    visit.status = "READY"
    db.commit()
    updated = service.record_post_visit(db, 4, "医生说继续观察血压，两周后复查。")
    assert updated.feedback_source == "doctor_reported_by_patient"
    assert updated.follow_up_date is not None
    task = db.scalar(select(CareTask).where(CareTask.source == "doctor", CareTask.member_id == 4))
    assert task is not None

