import json
import re
from datetime import date, datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import CareTask, FamilyMember, HealthLog, HealthProfile, Measurement, MedicalVisit
from app.services.weekly_summary import WeeklySummaryBuilder


class DoctorModeService:
    questions = {
        0: "这次看的是原来的医生，还是换了新医生？如果是原医生，请告诉我医生姓名。",
        1: "这次最想让医生帮你解决什么问题？",
        2: "这个情况大约什么时候开始的？",
        3: "最近总体是在变好、变差，还是反复波动？",
        4: "通常在什么情况下会更明显？",
        5: "同时还有别的不舒服吗？",
        6: "最近用药有什么新增、停用或调整吗？",
        7: "你最想向医生确认的一个问题是什么？",
    }

    def start(self, db: Session, member_id: int) -> MedicalVisit:
        profile = db.scalar(select(HealthProfile).where(HealthProfile.member_id == member_id))
        recent_measurements = list(db.scalars(select(Measurement).where(Measurement.member_id == member_id).order_by(desc(Measurement.measured_at)).limit(5)))
        recent_logs = list(db.scalars(select(HealthLog).where(HealthLog.member_id == member_id, HealthLog.occurred_at >= datetime.now() - timedelta(days=30)).order_by(desc(HealthLog.occurred_at))))
        sensitive_symptoms = self._extract_recent_sensitive_symptoms(recent_logs)
        visit = MedicalVisit(
            member_id=member_id,
            status="PREPARING",
            medical_history_snapshot=profile.known_conditions if profile else None,
            medication_snapshot=profile.medications if profile else None,
            measurement_summary=json.dumps([
                {"type": x.type, "value": x.value, "value2": x.value2, "unit": x.unit, "time": x.measured_at.isoformat()}
                for x in recent_measurements
            ], ensure_ascii=False),
            symptom_summary=json.dumps({"recent_sensitive_symptoms": sensitive_symptoms}, ensure_ascii=False) if sensitive_symptoms else None,
            conversation_step=0,
        )
        db.add(visit)
        db.commit()
        db.refresh(visit)
        return visit

    @staticmethod
    def _extract_recent_sensitive_symptoms(logs: list[HealthLog]) -> list[str]:
        """避免就医摘要遗漏遗精等容易被口语表达掩盖的敏感症状。"""
        results: list[str] = []
        for log in logs:
            try:
                data = json.loads(log.structured_data or "{}")
            except json.JSONDecodeError:
                data = {}
            sexual_health = str(data.get("sexual_health") or "")
            if sexual_health or any(x in log.raw_text for x in ("遗精", "梦遗")):
                normalized = "睡眠中遗精" if any(x in f"{sexual_health}{log.raw_text}" for x in ("遗精", "梦遗", "睡眠中")) else sexual_health
                item = f"{log.occurred_at:%Y-%m-%d}：{normalized or '性健康相关表现（详见原始记录）'}"
                if item not in results:
                    results.append(item)
        return results

    def continue_visit(self, db: Session, visit: MedicalVisit, text: str) -> tuple[str, bool]:
        step = visit.conversation_step
        answers = json.loads(visit.symptom_summary or "{}")
        keys = ["doctor_context", "chief_complaint", "start_time", "current_trend", "triggers", "associated_symptoms", "medication_changes", "question_for_doctor"]
        key = keys[min(step, len(keys) - 1)]
        answers[key] = text
        if step == 0:
            relation, doctor_name = self._normalize_doctor_context(text)
            answers["doctor_context_type"] = relation
            if doctor_name:
                answers["doctor_name"] = doctor_name
        visit.symptom_summary = json.dumps(answers, ensure_ascii=False)
        if step == 1:
            visit.chief_complaint = text
            visit.visit_reason = text
        if step == 7:
            visit.questions_for_doctor = text
            visit.status = "REVIEWING"
            visit.conversation_step = 7
            db.commit()
            return "情况已经整理好了。请先核对下面的清单，确认没有漏掉近期的变化后，我再生成正式《就医摘要》。", True
        visit.conversation_step += 1
        db.commit()
        return self.questions[visit.conversation_step], False

    @staticmethod
    def _normalize_doctor_context(text: str) -> tuple[str, str | None]:
        """把自由表达转成稳定枚举；先判断否定和换医生，避免“不是原医生”被误判为复诊。"""
        clean = text.strip()
        new_marks = ("不是原医生", "不是以前", "新医生", "换医生", "换了医生", "第一次看", "初诊")
        returning_marks = ("原医生", "原来的医生", "以前的医生", "还是以前", "复诊", "廖伯年")
        relation = "new" if any(x in clean for x in new_marks) else "returning" if any(x in clean for x in returning_marks) else "unknown"
        doctor_name = "廖伯年" if "廖伯年" in clean else None
        return relation, doctor_name

    def latest_active(self, db: Session, member_id: int) -> MedicalVisit | None:
        return db.scalar(select(MedicalVisit).where(MedicalVisit.member_id == member_id, MedicalVisit.status == "PREPARING").order_by(desc(MedicalVisit.created_at)).limit(1))

    def record_post_visit(self, db: Session, member_id: int, text: str) -> MedicalVisit:
        visit = db.scalar(select(MedicalVisit).where(MedicalVisit.member_id == member_id, MedicalVisit.status.in_(("READY", "VISITED", "FOLLOW_UP"))).order_by(desc(MedicalVisit.created_at)).limit(1))
        if not visit:
            visit = MedicalVisit(member_id=member_id, status="VISITED", visit_reason="就医后补录")
            db.add(visit)
            db.flush()
        visit.doctor_feedback = text
        visit.doctor_confirmed_plan = text
        visit.feedback_source = "doctor_reported_by_patient"
        visit.status = "FOLLOW_UP"
        follow_up = self._extract_follow_up(text)
        if follow_up:
            visit.follow_up_date = follow_up
            db.add(CareTask(member_id=member_id, task_type="follow_up", title="按医生要求复查", description=text, scheduled_at=datetime.combine(follow_up, datetime.min.time()).replace(hour=9), source="doctor"))
        db.commit()
        db.refresh(visit)
        return visit

    @staticmethod
    def _extract_follow_up(text: str) -> date | None:
        match = re.search(r"(\d+)\s*(天|周|个月|月)后.*复查|([一二两三四五六])\s*(天|周|个月|月)后.*复查", text)
        if not match:
            return None
        raw = match.group(1) or match.group(3)
        number = int(raw) if raw.isdigit() else {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6}[raw]
        unit = match.group(2) or match.group(4)
        days = number if unit == "天" else number * 7 if unit == "周" else number * 30
        return date.today() + timedelta(days=days)

    def summary(self, db: Session, visit: MedicalVisit) -> dict:
        member = db.get(FamilyMember, visit.member_id)
        profile = db.scalar(select(HealthProfile).where(HealthProfile.member_id == visit.member_id))
        age = None
        if member and member.birthday:
            age = date.today().year - member.birthday.year - ((date.today().month, date.today().day) < (member.birthday.month, member.birthday.day))
        details = json.loads(visit.symptom_summary or "{}")
        age_text = f"{age}岁" if age is not None else None
        if age_text is None and profile and profile.profile_data:
            try:
                age_text = json.loads(profile.profile_data).get("age_text")
            except json.JSONDecodeError:
                age_text = None
        doctor_context = str(details.get("doctor_context") or "")
        relation = str(details.get("doctor_context_type") or "")
        if relation not in ("returning", "new", "unknown"):
            relation, _ = self._normalize_doctor_context(doctor_context)
        returning_doctor = relation == "returning"
        return {
            "title": "原医生复诊简报" if returning_doctor or "原医生复诊" in (visit.visit_reason or "") else "新医生就诊摘要",
            "visit_id": visit.id,
            "name": member.name if member else "未知",
            "age": age,
            "age_text": age_text,
            "status": visit.status,
            "main_problem": visit.chief_complaint,
            "symptom_course": details,
            "known_conditions": visit.medical_history_snapshot,
            "medications": visit.medication_snapshot,
            "recent_measurements": json.loads(visit.measurement_summary or "[]"),
            "recent_reports": visit.report_summary,
            "questions_for_doctor": visit.questions_for_doctor,
            "doctor_feedback": visit.doctor_feedback,
            "doctor_feedback_source": visit.feedback_source,
            "follow_up_date": visit.follow_up_date.isoformat() if visit.follow_up_date else None,
            "disclaimer": "本摘要用于整理用户、家属或上传资料提供的信息，不构成诊断或用药建议。",
        }

    def update_review_answer(self, db: Session, visit: MedicalVisit, key: str, value: str) -> MedicalVisit:
        if visit.status != "REVIEWING":
            raise ValueError("只有待核对的摘要可以修改")
        allowed = {"doctor_context", "chief_complaint", "start_time", "current_trend", "triggers", "associated_symptoms", "medication_changes", "question_for_doctor"}
        if key not in allowed:
            raise ValueError("该项目不能在核对页修改")
        details = json.loads(visit.symptom_summary or "{}")
        details[key] = value.strip()
        if key == "doctor_context":
            relation, doctor_name = self._normalize_doctor_context(value)
            details["doctor_context_type"] = relation
            if doctor_name:
                details["doctor_name"] = doctor_name
            else:
                details.pop("doctor_name", None)
        elif key == "chief_complaint":
            visit.chief_complaint = value.strip()
            visit.visit_reason = value.strip()
        elif key == "question_for_doctor":
            visit.questions_for_doctor = value.strip()
        visit.symptom_summary = json.dumps(details, ensure_ascii=False)
        db.commit()
        db.refresh(visit)
        return visit

    @staticmethod
    def mark_shared_with_doctor(db: Session, visit: MedicalVisit) -> MedicalVisit:
        if visit.status not in ("READY", "VISITED", "FOLLOW_UP"):
            raise ValueError("请先完成并确认就医摘要")
        if visit.status == "READY":
            visit.status = "VISITED"
            db.commit()
            db.refresh(visit)
        return visit

    def review_checklist(self, db: Session, visit: MedicalVisit) -> dict:
        """生成正式报告前的核对清单：8 个问题答案 + 近 14 天原始记录分类。"""
        member = db.get(FamilyMember, visit.member_id)
        profile = db.scalar(select(HealthProfile).where(HealthProfile.member_id == visit.member_id))
        details = json.loads(visit.symptom_summary or "{}")
        weekly = WeeklySummaryBuilder().build(db, visit.member_id, days=14)
        answer_fields = [
            ("doctor_context", "就诊医生"),
            ("chief_complaint", "主要问题"),
            ("start_time", "开始时间"),
            ("current_trend", "近期总体趋势"),
            ("triggers", "明显场景"),
            ("associated_symptoms", "伴随情况"),
            ("medication_changes", "近期用药变化"),
            ("question_for_doctor", "想问医生"),
        ]
        answers = [{"key": key, "label": label, "value": str(details[key])} for key, label in answer_fields if details.get(key)]
        return {
            "visit_id": visit.id,
            "member_name": member.name if member else "未知",
            "status": visit.status,
            "answers": answers,
            "known_conditions": visit.medical_history_snapshot or (profile.known_conditions if profile else None),
            "medications": visit.medication_snapshot or (profile.medications if profile else None),
            "recent_sensitive_symptoms": details.get("recent_sensitive_symptoms") or [],
            "weekly": weekly,
            "disclaimer": "核对清单只用于整理用户、家属或上传资料提供的信息，不构成诊断或用药建议。",
        }

    def confirm_review(self, db: Session, visit: MedicalVisit) -> MedicalVisit:
        if visit.status != "REVIEWING":
            raise ValueError("当前没有待核对的就医摘要")
        visit.status = "READY"
        db.commit()
        db.refresh(visit)
        return visit
