from sqlalchemy import select

from app.models.entities import PendingAction
from app.services.familycare_agent import FamilyCareAgent


def test_contact_resolution_and_phone_confirmation(db):
    agent = FamilyCareAgent()
    first = agent.handle(db, 4, "给儿子打电话。", "phone-demo")
    assert first.data["confirmation_required"] is True
    assert "确定" in first.reply
    pending = db.scalar(select(PendingAction).where(PendingAction.session_id == "phone-demo"))
    assert pending.status == "pending"
    second = agent.handle(db, 4, "确定。", "phone-demo")
    assert "模拟拨号成功" in second.reply
    assert pending.status == "completed"


def test_phone_can_be_cancelled_without_calling(db):
    agent = FamilyCareAgent()
    agent.handle(db, 4, "给儿子打电话。", "cancel-demo")
    result = agent.handle(db, 4, "不打了。", "cancel-demo")
    assert "取消" in result.reply

