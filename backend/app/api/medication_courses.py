import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import MedicationCourse
from app.schemas.common import MedicationCourseCreate

router = APIRouter(prefix="/medication-courses", tags=["处方疗程"])


def _serialize(row: MedicationCourse) -> dict:
    return {
        "id": row.id,
        "member_id": row.member_id,
        "course_number": row.course_number,
        "prescription_date": row.prescription_date,
        "hospital": row.hospital,
        "department": row.department,
        "doctor": row.doctor,
        "formula_relation": row.formula_relation,
        "formula_data": json.loads(row.formula_data or "{}"),
        "dosage_instructions": row.dosage_instructions,
        "source_document_id": row.source_document_id,
        "raw_user_text": row.raw_user_text,
        "status": row.status,
    }


@router.get("")
def list_courses(member_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(select(MedicationCourse).where(MedicationCourse.member_id == member_id).order_by(MedicationCourse.course_number))
    return [_serialize(row) for row in rows]


@router.post("")
def upsert_course(payload: MedicationCourseCreate, db: Session = Depends(get_db)):
    row = db.scalar(select(MedicationCourse).where(MedicationCourse.member_id == payload.member_id, MedicationCourse.course_number == payload.course_number))
    data = payload.model_dump()
    data["formula_data"] = json.dumps(data["formula_data"], ensure_ascii=False)
    if row:
        for key, value in data.items():
            setattr(row, key, value)
    else:
        row = MedicationCourse(**data)
        db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize(row)
