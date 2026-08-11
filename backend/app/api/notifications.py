from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import EmergencyContact
from app.providers.notification import MockNotificationProvider
from app.schemas.common import FamilyNotificationIn

router = APIRouter(prefix="/notifications", tags=["家属通知"])


@router.post("/family")
def notify_family(payload: FamilyNotificationIn, db: Session = Depends(get_db)):
    if not payload.confirm:
        raise HTTPException(409, "发送重要信息需要二次确认：confirm=true")
    contacts = list(db.scalars(select(EmergencyContact).where(EmergencyContact.member_id == payload.member_id, EmergencyContact.can_receive_alert.is_(True)).order_by(EmergencyContact.priority)))
    if not contacts:
        raise HTTPException(404, "没有可接收提醒的家属联系人")
    recipients = [{"id": row.id, "name": row.name, "phone": row.phone} for row in contacts]
    return MockNotificationProvider().notify(recipients, payload.message)
