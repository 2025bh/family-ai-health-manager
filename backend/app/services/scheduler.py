from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.entities import CheckInSchedule, HealthLog


class CheckInScheduler:
    """主动询问调度骨架：时间可配置，并尊重跳过/稍后提醒。"""

    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.add_job(self.scan_due_checkins, "interval", minutes=1, id="checkins", replace_existing=True)
            self.scheduler.start()

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def scan_due_checkins(self) -> None:
        # V0.1 生成问题的逻辑可测试；真正推送由 Android/飞书通知 Provider 接入。
        with SessionLocal() as db:
            for schedule in db.scalars(select(CheckInSchedule)):
                self.next_question(db, schedule.member_id, datetime.now())

    def next_question(self, db, member_id: int, at: datetime) -> str | None:
        schedule = db.scalar(select(CheckInSchedule).where(CheckInSchedule.member_id == member_id))
        if not schedule or schedule.skip_today or (schedule.snooze_until and schedule.snooze_until > at):
            return None
        today_types = set(db.scalars(select(HealthLog.log_type).where(HealthLog.member_id == member_id, HealthLog.occurred_at >= at.replace(hour=0, minute=0, second=0, microsecond=0))))
        hm = at.strftime("%H:%M")
        if schedule.morning_enabled and hm >= schedule.morning_time and "sleep" not in today_types:
            return "早上好，昨晚睡得怎么样？"
        if schedule.afternoon_enabled and hm >= schedule.afternoon_time and "food" not in today_types:
            return "今天吃得怎么样？"
        if schedule.evening_enabled and hm >= schedule.evening_time and "symptom" not in today_types:
            return "今天身体感觉怎么样？"
        return None

