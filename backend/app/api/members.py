import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import FamilyMember, HealthProfile
from app.schemas.common import MemberCreate, MemberRead, MemberUpdate, ProfileUpdate
from app.services.context_builder import ContextBuilder
from app.services.timeline import build_timeline
from app.services.weekly_summary import build_weekly_summary

router = APIRouter(prefix="/members", tags=["家庭成员"])


@router.get("", response_model=list[MemberRead])
def list_members(db: Session = Depends(get_db)):
    return list(db.scalars(select(FamilyMember).order_by(FamilyMember.id)))


@router.post("", response_model=MemberRead)
def create_member(payload: MemberCreate, db: Session = Depends(get_db)):
    row = FamilyMember(**payload.model_dump())
    db.add(row)
    db.flush()
    db.add(HealthProfile(member_id=row.id))
    db.commit()
    db.refresh(row)
    return row


@router.put("/{member_id}", response_model=MemberRead)
def update_member(member_id: int, payload: MemberUpdate, db: Session = Depends(get_db)):
    row = db.get(FamilyMember, member_id)
    if not row:
        raise HTTPException(404, "家庭成员不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{member_id}")
def get_member(member_id: int, db: Session = Depends(get_db)):
    member = db.get(FamilyMember, member_id)
    if not member:
        raise HTTPException(404, "家庭成员不存在")
    return ContextBuilder().build(db, member_id)


@router.get("/{member_id}/profile")
def get_profile(member_id: int, db: Session = Depends(get_db)):
    row = db.scalar(select(HealthProfile).where(HealthProfile.member_id == member_id))
    if not row:
        raise HTTPException(404, "健康档案不存在")
    return row


@router.put("/{member_id}/profile")
def update_profile(payload: ProfileUpdate, member_id: int, confirm_sensitive: bool = Query(False), db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    if any(key in data for key in ("medications", "doctor_notes", "profile_data", "raw_profile_text")) and not confirm_sensitive:
        raise HTTPException(409, "修改用药或医生记录需要二次确认：confirm_sensitive=true")
    row = db.scalar(select(HealthProfile).where(HealthProfile.member_id == member_id))
    if not row:
        raise HTTPException(404, "健康档案不存在")
    if isinstance(data.get("profile_data"), dict):
        data["profile_data"] = json.dumps(data["profile_data"], ensure_ascii=False)
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{member_id}/timeline")
def timeline(member_id: int, db: Session = Depends(get_db)):
    if not db.get(FamilyMember, member_id):
        raise HTTPException(404, "家庭成员不存在")
    return build_timeline(db, member_id)


@router.get("/{member_id}/weekly-summary")
def weekly_summary(member_id: int, days: int = Query(7, ge=1, le=90), db: Session = Depends(get_db)):
    if not db.get(FamilyMember, member_id):
        raise HTTPException(404, "家庭成员不存在")
    return build_weekly_summary(db, member_id, days=days)
