import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import HealthLog, HealthLogRevision
from app.schemas.common import HealthLogCreate, HealthLogUpdate
from app.services.health_parser import HealthLogParser
from app.services.safety import SafetyService
from app.services.western_prevention import WesternPreventionEngine

router = APIRouter(prefix="/health-logs", tags=["健康日志"])


@router.get("")
def list_logs(member_id: int, limit: int = 50, db: Session = Depends(get_db)):
    rows = db.scalars(select(HealthLog).where(HealthLog.member_id == member_id).order_by(desc(HealthLog.occurred_at)).limit(min(limit, 200)))
    return [{"id": x.id, "member_id": x.member_id, "log_type": x.log_type, "raw_text": x.raw_text, "structured_data": json.loads(x.structured_data), "source": x.source, "possible_emergency": x.possible_emergency, "occurred_at": x.occurred_at} for x in rows]


@router.post("")
def create_log(payload: HealthLogCreate, db: Session = Depends(get_db)):
    if payload.source_key:
        existing = db.scalar(select(HealthLog).where(HealthLog.source_key == payload.source_key))
        if existing:
            return {"id": existing.id, "raw_text_preserved": existing.raw_text, "possible_emergency": existing.possible_emergency, "already_exists": True}
    risk = SafetyService().check_input(payload.raw_text)
    row = HealthLog(member_id=payload.member_id, log_type=payload.log_type, raw_text=payload.raw_text, structured_data=json.dumps(payload.structured_data, ensure_ascii=False), source=payload.source, source_key=payload.source_key, possible_emergency=risk.possible_emergency, **({"occurred_at": payload.occurred_at} if payload.occurred_at else {}))
    db.add(row)
    db.commit()
    db.refresh(row)
    WesternPreventionEngine().recompute(db, row.member_id, "health_log_created", row.id)
    return {"id": row.id, "raw_text_preserved": row.raw_text, "possible_emergency": row.possible_emergency}


@router.patch("/{log_id}")
def update_log(log_id: int, payload: HealthLogUpdate, db: Session = Depends(get_db)):
    row = db.get(HealthLog, log_id)
    if not row:
        raise HTTPException(404, "健康记录不存在")
    parsed = HealthLogParser().parse(payload.raw_text.strip())
    risk = SafetyService().check_input(payload.raw_text)
    db.add(HealthLogRevision(
        health_log_id=row.id,
        member_id=row.member_id,
        previous_raw_text=row.raw_text,
        previous_log_type=row.log_type,
        previous_structured_data=row.structured_data,
        previous_possible_emergency=row.possible_emergency,
    ))
    row.raw_text = payload.raw_text.strip()
    row.log_type = parsed.log_type
    row.structured_data = json.dumps(parsed.structured_data, ensure_ascii=False)
    row.possible_emergency = risk.possible_emergency
    db.commit()
    db.refresh(row)
    recomputed = WesternPreventionEngine().recompute(db, row.member_id, "health_log_corrected", row.id)
    return {"id": row.id, "raw_text_preserved": row.raw_text, "structured_data": parsed.structured_data, "possible_emergency": row.possible_emergency, "recomputed_periods": [x["period_days"] for x in recomputed["runs"]]}
