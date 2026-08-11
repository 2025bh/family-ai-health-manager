from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import MedicalRule, PreventionItem
from app.schemas.health_guard import HealthSettingUpdate, PreventionItemCreate, RecomputeRequest
from app.services.health_settings import HealthSettingService
from app.services.tcm_health import TcmHealthEngine
from app.services.western_prevention import WesternPreventionEngine

router = APIRouter(prefix="/health-guard", tags=["健康守护"])
settings_service = HealthSettingService()
western_engine = WesternPreventionEngine()


def setting_payload(row) -> dict:
    return {
        "member_id": row.member_id,
        "western_prevention_enabled": row.western_prevention_enabled,
        "tcm_health_enabled": row.tcm_health_enabled,
        "tcm_enabled_at": row.tcm_enabled_at,
        "tcm_consent_version": row.tcm_consent_version,
        "tcm_depth": row.tcm_depth,
        "tcm": TcmHealthEngine.describe(row),
        "medical_safety_always_enabled": True,
    }


@router.get("/settings")
def get_settings(member_id: int, db: Session = Depends(get_db)):
    try:
        return setting_payload(settings_service.get_or_create(db, member_id))
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.put("/settings")
def update_settings(member_id: int, payload: HealthSettingUpdate, db: Session = Depends(get_db)):
    try:
        return setting_payload(settings_service.update(db, member_id, payload.model_dump()))
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/analysis")
def get_analysis(member_id: int, days: int = Query(7), refresh: bool = False, db: Session = Depends(get_db)):
    if days not in (7, 30):
        raise HTTPException(400, "只支持7天或30天分析")
    setting = settings_service.get_or_create(db, member_id)
    if not setting.western_prevention_enabled:
        return {"member_id": member_id, "engine": "western", "enabled": False, "results": []}
    result = None if refresh else western_engine.latest(db, member_id, days)
    return result or western_engine.generate(db, member_id, days, "initial_view")


@router.post("/recompute")
def recompute(payload: RecomputeRequest, db: Session = Depends(get_db)):
    settings_service.get_or_create(db, payload.member_id)
    return western_engine.recompute(db, payload.member_id, payload.trigger_type, payload.trigger_source_id)


@router.get("/rules")
def list_rules(db: Session = Depends(get_db)):
    rows = db.scalars(select(MedicalRule).where(MedicalRule.enabled.is_(True)).order_by(MedicalRule.category, MedicalRule.rule_id))
    return [{"rule_id": x.rule_id, "rule_name": x.rule_name, "rule_version": x.rule_version, "category": x.category, "risk_level": x.risk_level, "escalation_action": x.escalation_action, "source": x.source, "reviewed_at": x.reviewed_at} for x in rows]


@router.get("/prevention-items")
def list_prevention_items(member_id: int, db: Session = Depends(get_db)):
    return list(db.scalars(select(PreventionItem).where(PreventionItem.member_id == member_id).order_by(desc(PreventionItem.created_at))))


@router.post("/prevention-items")
def create_prevention_item(payload: PreventionItemCreate, db: Session = Depends(get_db)):
    if payload.source_type not in {"doctor_feedback", "medical_document", "user_confirmed", "medical_rule"}:
        raise HTTPException(400, "预防事项必须绑定明确来源，不能由系统自由编造")
    row = PreventionItem(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
