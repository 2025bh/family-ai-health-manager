from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import MedicalRule


BASELINE_RULES = (
    {
        "rule_id": "MSL-BLEEDING-001",
        "rule_name": "当前本人消化道出血相关表达",
        "category": "medical_safety",
        "condition": {"phrases": ["黑便", "黑色大便", "便血", "呕血"], "requires": ["self", "current", "affirmed"]},
        "risk_level": "red",
        "escalation_action": "seek_timely_medical_evaluation",
    },
    {
        "rule_id": "MSL-ABDOMEN-001",
        "rule_name": "当前本人剧烈腹痛相关表达",
        "category": "medical_safety",
        "condition": {"phrases": ["剧烈腹痛", "绞痛"], "requires": ["self", "current", "affirmed"]},
        "risk_level": "red",
        "escalation_action": "seek_timely_medical_evaluation",
    },
    {
        "rule_id": "WPE-TREND-001",
        "rule_name": "近期症状记录较上一周期增加",
        "category": "trend",
        "condition": {"logic": "current_distinct_days >= baseline_distinct_days + 2 and current_distinct_days >= 2"},
        "risk_level": "yellow",
        "escalation_action": "schedule_medical_review",
    },
    {
        "rule_id": "WPE-DATA-001",
        "rule_name": "趋势数据不足",
        "category": "data_quality",
        "condition": {"logic": "current_count + baseline_count < 2"},
        "risk_level": "insufficient_data",
        "escalation_action": "continue_monitoring",
    },
)


class MedicalRuleService:
    RULE_VERSION = "1.0"
    SOURCE = "FamilyCare V0.2 内部保守基线；尚待医疗专业人员逐条审核，不作为临床诊断标准"

    def ensure_baseline(self, db: Session) -> None:
        for item in BASELINE_RULES:
            exists = db.scalar(select(MedicalRule).where(MedicalRule.rule_id == item["rule_id"], MedicalRule.rule_version == self.RULE_VERSION))
            if exists:
                continue
            db.add(MedicalRule(
                rule_id=item["rule_id"], rule_name=item["rule_name"], rule_version=self.RULE_VERSION,
                category=item["category"], condition=json.dumps(item["condition"], ensure_ascii=False),
                risk_level=item["risk_level"], escalation_action=item["escalation_action"],
                source=self.SOURCE, reviewed_at=None, enabled=True,
            ))
        db.commit()
