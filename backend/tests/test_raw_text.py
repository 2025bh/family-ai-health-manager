from sqlalchemy import select

from app.models.entities import HealthLog
from app.services.familycare_agent import FamilyCareAgent


def test_agent_never_discards_elder_raw_expression(db):
    raw = "昨晚胸口有点不得劲。"
    FamilyCareAgent().handle(db, 4, raw, "raw-demo")
    row = db.scalar(select(HealthLog).where(HealthLog.raw_text == raw))
    assert row is not None
    assert "胸部不适" in row.structured_data

