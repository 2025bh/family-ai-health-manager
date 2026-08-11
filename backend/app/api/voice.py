from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import FamilyMember
from app.providers.voice import WebVoiceGateway, XiaozhiVoiceGateway
from app.schemas.common import VoiceMessageIn, VoiceMessageOut
from app.services.familycare_agent import FamilyCareAgent

router = APIRouter(prefix="/voice", tags=["语音模拟器"])
agent = FamilyCareAgent()


@router.post("/message", response_model=VoiceMessageOut)
def voice_message(payload: VoiceMessageIn, db: Session = Depends(get_db)):
    if not db.get(FamilyMember, payload.member_id):
        raise HTTPException(404, "家庭成员不存在")
    gateway = XiaozhiVoiceGateway() if payload.gateway == "xiaozhi" else WebVoiceGateway()
    return agent.handle(db, payload.member_id, gateway.normalize(payload.text), payload.session_id)

