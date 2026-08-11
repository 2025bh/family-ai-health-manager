from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import CareTask, CheckInSchedule
from app.schemas.common import ScheduleUpdate, TaskCreate, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["健康任务"])


@router.get("")
def list_tasks(member_id: int, db: Session = Depends(get_db)):
    return list(db.scalars(select(CareTask).where(CareTask.member_id == member_id).order_by(CareTask.scheduled_at)))


@router.post("")
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    row = CareTask(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{task_id}")
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    row = db.get(CareTask, task_id)
    if not row:
        raise HTTPException(404, "健康任务不存在")
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] not in ("pending", "completed"):
        raise HTTPException(400, "任务状态只能是待完成或已完成")
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.get("/schedule/{member_id}")
def get_schedule(member_id: int, db: Session = Depends(get_db)):
    return db.scalar(select(CheckInSchedule).where(CheckInSchedule.member_id == member_id))


@router.put("/schedule/{member_id}")
def update_schedule(member_id: int, payload: ScheduleUpdate, db: Session = Depends(get_db)):
    row = db.scalar(select(CheckInSchedule).where(CheckInSchedule.member_id == member_id))
    if not row:
        row = CheckInSchedule(member_id=member_id)
        db.add(row)
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row
