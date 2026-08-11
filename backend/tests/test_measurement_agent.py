from sqlalchemy import select

from app.models.entities import Measurement
from app.services.familycare_agent import FamilyCareAgent


def test_blood_glucose_requires_context_then_creates_measurement(db):
    agent = FamilyCareAgent()
    first = agent.handle(db, 4, "今天血糖8.1。", "measurement-demo")
    assert "空腹" in first.reply and "饭后" in first.reply
    assert db.scalar(select(Measurement).where(Measurement.value == 8.1)) is None
    second = agent.handle(db, 4, "空腹测的。", "measurement-demo")
    row = db.scalar(select(Measurement).where(Measurement.value == 8.1))
    assert row is not None
    assert row.measurement_context == "fasting"
    assert "记好了" in second.reply

