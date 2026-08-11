import json
import re
import uuid

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import ConversationMessage, EmergencyContact, MedicalVisit, PendingAction
from app.providers.phone import MockPhoneProvider
from app.schemas.common import VoiceMessageOut
from app.services.care_tools import CareTools
from app.services.doctor_mode import DoctorModeService
from app.services.health_parser import HealthLogParser, MeasurementParser
from app.services.intent_router import Intent, IntentRouter
from app.services.safety import SafetyService


class FamilyCareAgent:
    """统一编排：Intent → Context → Safety → Tools → Database → Reply。"""

    def __init__(self) -> None:
        self.router = IntentRouter()
        self.safety = SafetyService()
        self.tools = CareTools()
        self.doctor = DoctorModeService()
        self.health_parser = HealthLogParser()
        self.measurement_parser = MeasurementParser()
        self.phone = MockPhoneProvider()

    def handle(self, db: Session, member_id: int, text: str, session_id: str | None = None) -> VoiceMessageOut:
        session_id = session_id or uuid.uuid4().hex
        clean_text = text.strip()
        self._message(db, member_id, session_id, "user", clean_text, None)

        safety = self.safety.check_input(clean_text)
        if safety.possible_emergency:
            self.tools.create_health_log(db, member_id, clean_text, "symptom", {"description": clean_text, "safety_reason": safety.reason}, "user_reported")
            reply = self.safety.emergency_reply()
            self._message(db, member_id, session_id, "assistant", reply, "SAFETY_ESCALATION")
            return VoiceMessageOut(session_id=session_id, intent="SAFETY_ESCALATION", reply=reply, possible_emergency=True, actions=[{"type": "contact_family"}, {"type": "contact_medical_service"}])

        pending = db.scalar(select(PendingAction).where(PendingAction.member_id == member_id, PendingAction.session_id == session_id, PendingAction.status == "pending").order_by(desc(PendingAction.created_at)).limit(1))
        if pending:
            return self._handle_pending(db, pending, member_id, clean_text, session_id)

        active_visit = self.doctor.latest_active(db, member_id)
        if active_visit:
            reply, complete = self.tools.update_medical_visit(db, active_visit, clean_text)
            self._message(db, member_id, session_id, "assistant", reply, Intent.CONTINUE_DOCTOR_MODE, active_visit.id)
            actions = [{"type": "view_visit", "visit_id": active_visit.id}] if complete else []
            return VoiceMessageOut(session_id=session_id, intent=Intent.CONTINUE_DOCTOR_MODE, reply=reply, actions=actions, data={"visit_id": active_visit.id, "complete": complete})

        intent = self.router.route(clean_text)
        if intent == Intent.START_DOCTOR_MODE:
            visit = self.tools.start_medical_visit(db, member_id)
            reply = self.doctor.questions[0]
            self._message(db, member_id, session_id, "assistant", reply, intent, visit.id)
            return VoiceMessageOut(session_id=session_id, intent=intent, reply=reply, data={"visit_id": visit.id})
        if intent == Intent.POST_VISIT:
            pending = PendingAction(member_id=member_id, session_id=session_id, action_type="post_visit_feedback", payload="{}")
            db.add(pending)
            db.commit()
            reply = "好的，医生今天怎么说？我只会按你的原话记录，并标注为‘患者转述医生意见’。"
            self._message(db, member_id, session_id, "assistant", reply, intent)
            return VoiceMessageOut(session_id=session_id, intent=intent, reply=reply)
        if intent == Intent.RECORD_MEASUREMENT:
            return self._measurement(db, member_id, clean_text, session_id, intent)
        if intent == Intent.CALL_CONTACT:
            return self._call_contact(db, member_id, clean_text, session_id, intent)
        if intent == Intent.VIEW_HEALTH_HISTORY:
            context = self.tools.get_member_health_context(db, member_id)
            count = len(context["recent_logs"])
            latest = context["recent_logs"][0]["raw_text"] if count else "暂无记录"
            reply = f"近30天有 {count} 条健康日志。最近一条是：{latest}。"
            self._message(db, member_id, session_id, "assistant", reply, intent)
            return VoiceMessageOut(session_id=session_id, intent=intent, reply=reply, actions=[{"type": "view_timeline", "member_id": member_id}], data=context)
        if intent == Intent.DAILY_HEALTH_LOG:
            parsed = self.health_parser.parse(clean_text)
            row = self.tools.create_health_log(db, member_id, clean_text, parsed.log_type, parsed.structured_data)
            recent_same = [x for x in self.tools.get_recent_health_logs(db, member_id, 10) if x.log_type == parsed.log_type]
            history_hint = "我也找到了之前的同类记录，会一起放进健康时间线。" if len(recent_same) > 1 else "这是第一条同类记录。"
            reply = f"好，我按你的原话记下了：‘{clean_text}’。{history_hint} 还有什么情况想补充吗？"
            self._message(db, member_id, session_id, "assistant", reply, intent)
            return VoiceMessageOut(session_id=session_id, intent=intent, reply=reply, data={"health_log_id": row.id, "structured_data": parsed.structured_data})
        reply = "我在听。你可以告诉我今天身体、睡眠、吃饭或运动怎么样，也可以说‘我要去看医生’。"
        self._message(db, member_id, session_id, "assistant", reply, intent)
        return VoiceMessageOut(session_id=session_id, intent=intent, reply=reply)

    def _measurement(self, db: Session, member_id: int, text: str, session_id: str, intent: Intent) -> VoiceMessageOut:
        data = self.measurement_parser.parse(text)
        if not data:
            reply = "我听到了测量信息，但没有识别出数值。可以再说一遍具体数值吗？"
            return VoiceMessageOut(session_id=session_id, intent=intent, reply=reply)
        if data["type"] == "blood_glucose" and data["measurement_context"] == "unknown":
            pending = PendingAction(member_id=member_id, session_id=session_id, action_type="measurement_context", payload=json.dumps({"raw_text": text, "data": data}, ensure_ascii=False))
            db.add(pending)
            db.commit()
            reply = "这是空腹测的，还是饭后测的？"
            self._message(db, member_id, session_id, "assistant", reply, intent)
            return VoiceMessageOut(session_id=session_id, intent=intent, reply=reply)
        row = self.tools.create_measurement(db, member_id, text, data)
        reply = f"记好了：{data['type']} {data['value']:g} {data['unit']}。"
        self._message(db, member_id, session_id, "assistant", reply, intent)
        return VoiceMessageOut(session_id=session_id, intent=intent, reply=reply, data={"measurement_id": row.id})

    def _call_contact(self, db: Session, member_id: int, text: str, session_id: str, intent: Intent) -> VoiceMessageOut:
        contacts = list(db.scalars(select(EmergencyContact).where(EmergencyContact.member_id == member_id).order_by(EmergencyContact.priority)))
        target = next((x for x in contacts if x.name in text or x.relationship in text), contacts[0] if len(contacts) == 1 else None)
        if not target:
            reply = "我没有找到唯一联系人。请说联系人姓名或关系，例如‘给儿子打电话’。"
            return VoiceMessageOut(session_id=session_id, intent=intent, reply=reply)
        pending = PendingAction(member_id=member_id, session_id=session_id, action_type="call_contact", payload=json.dumps({"contact_id": target.id}, ensure_ascii=False))
        db.add(pending)
        db.commit()
        reply = f"要给{target.name}打电话吗？请说‘确定’后我再执行。"
        self._message(db, member_id, session_id, "assistant", reply, intent)
        return VoiceMessageOut(session_id=session_id, intent=intent, reply=reply, data={"contact_id": target.id, "confirmation_required": True})

    def _handle_pending(self, db: Session, pending: PendingAction, member_id: int, text: str, session_id: str) -> VoiceMessageOut:
        if pending.action_type == "measurement_context":
            payload = json.loads(pending.payload)
            if "空腹" in text:
                payload["data"]["measurement_context"] = "fasting"
            elif any(x in text for x in ("饭后", "餐后")):
                payload["data"]["measurement_context"] = "post_meal"
            else:
                reply = "请告诉我是‘空腹’还是‘饭后’测的；如果不清楚，可以说‘不知道’。"
                if "不知道" in text:
                    payload["data"]["measurement_context"] = "unknown"
                else:
                    return VoiceMessageOut(session_id=session_id, intent=Intent.RECORD_MEASUREMENT, reply=reply)
            row = self.tools.create_measurement(db, member_id, payload["raw_text"], payload["data"])
            pending.status = "completed"
            db.commit()
            reply = f"记好了：血糖 {payload['data']['value']:g} mmol/L，测量状态是{self._context_label(payload['data']['measurement_context'])}。"
            return VoiceMessageOut(session_id=session_id, intent=Intent.RECORD_MEASUREMENT, reply=reply, data={"measurement_id": row.id})
        if pending.action_type == "post_visit_feedback":
            visit = self.tools.record_doctor_feedback(db, member_id, text)
            pending.status = "completed"
            db.commit()
            reply = "我已按你的原话记录医生交代，并标注了来源。若内容里有复查时间，也已经生成健康任务。"
            return VoiceMessageOut(session_id=session_id, intent=Intent.POST_VISIT, reply=reply, actions=[{"type": "view_visit", "visit_id": visit.id}], data={"visit_id": visit.id})
        if pending.action_type == "call_contact":
            confirmed = any(x in text for x in ("确定", "确认", "打吧", "打电话", "好"))
            if not confirmed:
                pending.status = "cancelled"
                db.commit()
                return VoiceMessageOut(session_id=session_id, intent=Intent.CALL_CONTACT, reply="好的，已经取消，没有拨号。")
            contact = db.get(EmergencyContact, json.loads(pending.payload)["contact_id"])
            reply = self.phone.call(contact.name, contact.phone)
            pending.status = "completed"
            db.commit()
            return VoiceMessageOut(session_id=session_id, intent=Intent.CALL_CONTACT, reply=reply, data={"mock": True})
        return VoiceMessageOut(session_id=session_id, intent=Intent.UNKNOWN, reply="这一步已失效，请重新说一次。")

    @staticmethod
    def _message(db: Session, member_id: int, session_id: str, role: str, text: str, intent, visit_id: int | None = None) -> None:
        db.add(ConversationMessage(member_id=member_id, session_id=session_id, visit_id=visit_id, role=role, text=text, intent=str(intent) if intent else None))
        db.commit()

    @staticmethod
    def _context_label(value: str) -> str:
        return {"fasting": "空腹", "post_meal": "饭后", "random": "随机", "unknown": "不清楚"}.get(value, value)

