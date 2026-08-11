import json
import re
from datetime import datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import FamilyMember, HealthLog, Measurement

CATEGORY_LABELS = [
    ("sleep", "睡眠"),
    ("digestive", "胃肠与排便"),
    ("energy", "精力"),
    ("weight", "体重"),
    ("blood_pressure", "血压"),
    ("blood_glucose", "血糖"),
    ("mood", "情绪"),
    ("oral", "口腔"),
    ("sexual_health", "遗精 / 性健康"),
    ("medication_change", "用药变化"),
    ("other", "其他记录"),
]

MEDICATION_MARKS = ("停用", "停药", "加量", "减量", "新增", "调整", "换方", "改方", "加药", "减药", "开始服", "改服", "加了", "减了", "停了")
SEXUAL_MARKS = ("遗精", "梦遗", "射精", "射了")
DIGESTIVE_MARKS = ("便", "拉", "胃", "肠", "消化", "呕")
ENERGY_MARKS = ("精力", "乏力", "没劲", "困", "累")
ORAL_MARKS = ("口腔", "牙龈", "溃疡", "口干", "上火", "口苦")
MOOD_MARKS = ("心情", "抑郁", "焦虑", "情绪", "开心", "难过", "烦", "胡思乱想")
SLEEP_MARKS = ("睡", "醒", "失眠", "入睡")
WEIGHT_MARKS = ("体重",)
CATEGORY_MARKS = {
    "sleep": SLEEP_MARKS,
    "digestive": DIGESTIVE_MARKS,
    "energy": ENERGY_MARKS,
    "weight": WEIGHT_MARKS,
    "mood": MOOD_MARKS,
    "oral": ORAL_MARKS,
    "sexual_health": SEXUAL_MARKS,
    "medication_change": MEDICATION_MARKS + ("服药", "中药", "焦虑药", "益生菌"),
}


class WeeklySummaryBuilder:
    """按固定口径汇总最近 N 天日志与测量，供首页摘要和看医生核对复用。"""

    def build(self, db: Session, member_id: int, days: int = 7) -> dict:
        member = db.get(FamilyMember, member_id)
        if not member:
            raise ValueError("家庭成员不存在")
        end = datetime.now().replace(microsecond=0)
        start = end - timedelta(days=days)
        logs = list(db.scalars(select(HealthLog).where(HealthLog.member_id == member_id, HealthLog.occurred_at >= start).order_by(desc(HealthLog.occurred_at))))
        measurements = list(db.scalars(select(Measurement).where(Measurement.member_id == member_id, Measurement.measured_at >= start).order_by(desc(Measurement.measured_at))))
        categories: dict[str, dict] = {key: {"label": label, "items": []} for key, label in CATEGORY_LABELS}
        for log in logs:
            data = self._loads(log.structured_data)
            for key in self._log_categories(log, data):
                categories[key]["items"].append({
                    "date": log.occurred_at.date().isoformat(),
                    "time": log.occurred_at.isoformat(),
                    "raw_text": log.raw_text,
                    "summary_text": self._category_excerpt(log.raw_text, key),
                    "detail": self._log_detail(log, data),
                    "emergency": log.possible_emergency,
                })
        for m in measurements:
            detail = f"{m.type} {m.value:g}" + (f"/{m.value2:g}" if m.value2 is not None else "") + f" {m.unit}"
            if m.measurement_context != "unknown":
                detail += f"（{self._context_label(m.measurement_context)}）"
            item = {
                "date": m.measured_at.date().isoformat(),
                "time": m.measured_at.isoformat(),
                "raw_text": m.raw_text,
                "summary_text": detail,
                "detail": detail,
                "emergency": False,
            }
            categories[self._measurement_category(m)]["items"].append(item)
        return {
            "member_id": member.id,
            "member_name": member.name,
            "days": days,
            "start_date": start.date().isoformat(),
            "end_date": end.date().isoformat(),
            "log_count": len(logs),
            "measurement_count": len(measurements),
            "categories": [{"key": key, "label": label, "items": categories[key]["items"]} for key, label in CATEGORY_LABELS],
        }

    @staticmethod
    def _loads(value: str | None) -> dict:
        if not value:
            return {}
        try:
            data = json.loads(value)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _log_categories(self, log: HealthLog, data: dict) -> list[str]:
        """一条记录可能同时涉及多个主题（如当天既讲睡眠又讲排便）。"""
        text = log.raw_text
        keys: list[str] = []
        if data.get("sexual_health") or any(x in text for x in SEXUAL_MARKS):
            keys.append("sexual_health")
        if any(x in text for x in MEDICATION_MARKS):
            keys.append("medication_change")
        if log.log_type == "sleep" or any(x in text for x in SLEEP_MARKS):
            keys.append("sleep")
        mood_text = text.replace("焦虑药", "").replace("抗焦虑药", "").replace("氟哌噻吨美利曲辛片", "")
        # 旧解析器可能因“焦虑药”三个字把纯用药记录存成 mood；展示时仍以去除药名后的真实情绪词为准。
        if any(x in mood_text for x in MOOD_MARKS):
            keys.append("mood")
        if any(x in text for x in DIGESTIVE_MARKS):
            keys.append("digestive")
        if any(x in text for x in ENERGY_MARKS):
            keys.append("energy")
        if any(x in text for x in ORAL_MARKS):
            keys.append("oral")
        if any(x in text for x in WEIGHT_MARKS):
            keys.append("weight")
        return keys if keys else ["other"]

    @staticmethod
    def _category_excerpt(text: str, key: str) -> str:
        """按主题截取相关短句，避免同一篇长日记在多个卡片里整段重复。"""
        if key == "other":
            return text[:180] + ("…" if len(text) > 180 else "")
        marks = CATEGORY_MARKS.get(key, ())
        clauses = [x.strip(" ，。；") for x in re.split(r"[。；]", text) if x.strip(" ，。；")]
        matched = [x for x in clauses if any(mark in x for mark in marks)]
        excerpt = "；".join(matched[:2]) or text
        return excerpt[:180] + ("…" if len(excerpt) > 180 else "")

    @staticmethod
    def _measurement_category(m: Measurement) -> str:
        if m.type == "weight":
            return "weight"
        if m.type == "blood_pressure":
            return "blood_pressure"
        if m.type == "blood_glucose":
            return "blood_glucose"
        return "other"

    @staticmethod
    def _log_detail(log: HealthLog, data: dict) -> str:
        parts: list[str] = []
        if data.get("night_wakings"):
            parts.append(f"夜里起来{data['night_wakings']}次")
        if data.get("symptom"):
            parts.append(f"症状：{data['symptom']}")
        if data.get("duration"):
            parts.append(f"持续：{data['duration']}")
        if data.get("trigger"):
            parts.append(f"场景：{data['trigger']}")
        if data.get("sleep_time"):
            parts.append(f"入睡：{data['sleep_time']}")
        if data.get("description") and str(data["description"]) != log.raw_text:
            parts.append(str(data["description"]))
        return "；".join(parts) if parts else "已按原话记录"

    @staticmethod
    def _context_label(value: str) -> str:
        return {"fasting": "空腹", "post_meal": "饭后", "resting": "静息", "random": "随机", "unknown": "状态待确认"}.get(value, value)


def build_weekly_summary(db: Session, member_id: int, days: int = 7) -> dict:
    return WeeklySummaryBuilder().build(db, member_id, days=days)
