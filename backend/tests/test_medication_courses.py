import json
from datetime import date

from app.api.medication_courses import list_courses, upsert_course
from app.schemas.common import MedicationCourseCreate
from app.api.health_logs import create_log
from app.schemas.common import HealthLogCreate


def test_medication_course_upsert_is_idempotent(db):
    payload = MedicationCourseCreate(member_id=1, course_number=1, prescription_date=date(2026, 5, 15), formula_relation="首方", formula_data={"ingredients": ["法半夏"]})
    first = upsert_course(payload, db)
    second = upsert_course(payload.model_copy(update={"formula_relation": "同方复诊"}), db)
    rows = list_courses(1, db)
    assert first["id"] == second["id"]
    assert len(rows) == 1
    assert rows[0]["formula_relation"] == "同方复诊"
    assert rows[0]["formula_data"]["ingredients"] == ["法半夏"]


def test_historical_health_log_accepts_date_and_is_idempotent(db):
    from datetime import datetime

    payload = HealthLogCreate(member_id=1, log_type="medication_reaction", raw_text="饭后腹胀", source_key="diary-2026-05-16", occurred_at=datetime(2026, 5, 16, 20, 0))
    first = create_log(payload, db)
    second = create_log(payload, db)
    assert first["id"] == second["id"]
    assert second["already_exists"] is True
