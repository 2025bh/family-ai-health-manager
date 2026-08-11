from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import MedicalVisit
from app.schemas.common import VisitReviewUpdate
from app.services.doctor_mode import DoctorModeService

router = APIRouter(prefix="/visits", tags=["就医"])
service = DoctorModeService()


@router.get("")
def list_visits(member_id: int, db: Session = Depends(get_db)):
    return list(db.scalars(select(MedicalVisit).where(MedicalVisit.member_id == member_id).order_by(desc(MedicalVisit.created_at))))


@router.post("/start/{member_id}")
def start_visit(member_id: int, db: Session = Depends(get_db)):
    visit = service.start(db, member_id)
    return {"visit_id": visit.id, "status": visit.status, "question": service.questions[0]}


@router.get("/{visit_id}")
def visit_summary(visit_id: int, db: Session = Depends(get_db)):
    visit = db.get(MedicalVisit, visit_id)
    if not visit:
        raise HTTPException(404, "就医记录不存在")
    return service.summary(db, visit)


@router.get("/{visit_id}/review")
def visit_review_checklist(visit_id: int, db: Session = Depends(get_db)):
    visit = db.get(MedicalVisit, visit_id)
    if not visit:
        raise HTTPException(404, "就医记录不存在")
    return service.review_checklist(db, visit)


@router.post("/{visit_id}/confirm")
def confirm_visit(visit_id: int, db: Session = Depends(get_db)):
    visit = db.get(MedicalVisit, visit_id)
    if not visit:
        raise HTTPException(404, "就医记录不存在")
    try:
        service.confirm_review(db, visit)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"visit_id": visit.id, "status": visit.status}


@router.patch("/{visit_id}/review")
def update_visit_review(visit_id: int, payload: VisitReviewUpdate, db: Session = Depends(get_db)):
    visit = db.get(MedicalVisit, visit_id)
    if not visit:
        raise HTTPException(404, "就医记录不存在")
    try:
        service.update_review_answer(db, visit, payload.key, payload.value)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return service.review_checklist(db, visit)


@router.post("/{visit_id}/shared-with-doctor")
def mark_shared_with_doctor(visit_id: int, db: Session = Depends(get_db)):
    visit = db.get(MedicalVisit, visit_id)
    if not visit:
        raise HTTPException(404, "就医记录不存在")
    try:
        service.mark_shared_with_doctor(db, visit)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"visit_id": visit.id, "status": visit.status}
