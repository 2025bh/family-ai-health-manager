import json
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import (
    CareTask,
    CheckInSchedule,
    EmergencyContact,
    FamilyMember,
    HealthLog,
    HealthProfile,
    Measurement,
    MedicalVisit,
)


def seed_demo(db: Session) -> None:
    """只写完全虚构的演示家庭，不包含用户真实医疗数据。"""
    if db.scalar(select(FamilyMember.id).limit(1)):
        return

    members = [
        FamilyMember(name="我", relationship="本人", preferred_name="我"),
        FamilyMember(name="爸爸", relationship="父亲", preferred_name="爸"),
        FamilyMember(name="妈妈", relationship="母亲", preferred_name="妈"),
        FamilyMember(name="爷爷", relationship="祖父", preferred_name="爷爷", birthday=date(1948, 3, 8)),
    ]
    db.add_all(members)
    db.flush()
    profiles = {}
    for member in members:
        profile = HealthProfile(member_id=member.id)
        db.add(profile)
        profiles[member.id] = profile
        db.add(CheckInSchedule(member_id=member.id))

    grandpa = members[3]
    profiles[grandpa.id].known_conditions = "高血压（演示数据）"
    profiles[grandpa.id].medications = "演示用长期药物记录，需就医时由家属确认"
    now = datetime.now().replace(microsecond=0)
    db.add_all(
        [
            HealthLog(member_id=grandpa.id, log_type="sleep", raw_text="昨晚睡得一般，起来两次。", structured_data=json.dumps({"night_wakings": 2}, ensure_ascii=False), occurred_at=now - timedelta(days=4)),
            HealthLog(member_id=grandpa.id, log_type="symptom", raw_text="今天起床时有一点头晕。", structured_data=json.dumps({"symptom": "头晕", "trigger": "起床"}, ensure_ascii=False), occurred_at=now - timedelta(days=3)),
            Measurement(member_id=grandpa.id, type="blood_pressure", value=132, value2=82, unit="mmHg", measurement_context="resting", raw_text="血压132/82", measured_at=now - timedelta(days=2)),
            Measurement(member_id=grandpa.id, type="blood_glucose", value=7.2, unit="mmol/L", measurement_context="fasting", raw_text="空腹血糖7.2", measured_at=now - timedelta(days=1)),
            MedicalVisit(member_id=grandpa.id, status="CLOSED", visit_reason="例行复查（演示数据）", chief_complaint="血压复查", doctor_feedback="老人转述：医生让继续观察血压。", feedback_source="doctor_reported_by_patient", follow_up_date=date.today() + timedelta(days=30)),
            CareTask(member_id=grandpa.id, task_type="measurement", title="记录早晨血压", description="演示提醒", scheduled_at=now + timedelta(days=1), recurrence="daily", source="system"),
            EmergencyContact(member_id=grandpa.id, name="黄金周（演示）", relationship="儿子", phone="10000000000", priority=1),
        ]
    )
    db.commit()
