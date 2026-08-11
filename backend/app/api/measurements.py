from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import Measurement
from app.schemas.common import MeasurementCreate
from app.services.western_prevention import WesternPreventionEngine

router = APIRouter(prefix="/measurements", tags=["健康测量"])


@router.get("")
def list_measurements(member_id: int, limit: int = 50, db: Session = Depends(get_db)):
    return list(db.scalars(select(Measurement).where(Measurement.member_id == member_id).order_by(desc(Measurement.measured_at)).limit(min(limit, 200))))


@router.post("")
def create_measurement(payload: MeasurementCreate, db: Session = Depends(get_db)):
    row = Measurement(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    WesternPreventionEngine().recompute(db, row.member_id, "measurement_created", row.id)
    return row
