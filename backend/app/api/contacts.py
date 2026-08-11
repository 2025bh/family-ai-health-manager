from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import EmergencyContact
from app.schemas.common import ContactCreate

router = APIRouter(prefix="/contacts", tags=["联系人"])


@router.get("")
def list_contacts(member_id: int, db: Session = Depends(get_db)):
    return list(db.scalars(select(EmergencyContact).where(EmergencyContact.member_id == member_id).order_by(EmergencyContact.priority)))


@router.post("")
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)):
    row = EmergencyContact(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

