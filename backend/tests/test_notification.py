import pytest
from fastapi import HTTPException

from app.api.notifications import notify_family
from app.schemas.common import FamilyNotificationIn


def test_family_notification_requires_confirmation(db):
    with pytest.raises(HTTPException) as error:
        notify_family(FamilyNotificationIn(member_id=4, message="请关注爷爷今天的健康记录"), db)
    assert error.value.status_code == 409


def test_confirmed_family_notification_uses_mock(db):
    result = notify_family(FamilyNotificationIn(member_id=4, message="请关注爷爷今天的健康记录", confirm=True), db)
    assert result["provider"] == "mock"
    assert result["sent"] == 1
    assert "未发送到真实手机" in result["message"]
