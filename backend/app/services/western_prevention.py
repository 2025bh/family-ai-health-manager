from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
import json

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import HealthAnalysisResult, HealthAnalysisRun, HealthEvidence, HealthLog, Measurement
from app.services.medical_rules import MedicalRuleService
from app.services.medical_safety import MedicalSafetyLayer


CATEGORIES = {
    "digestive": ("胃肠", ("胀", "反流", "烧心", "胃疼", "胃痛", "恶心", "打嗝", "不容易饿"), "negative"),
    "bowel": ("排便", ("腹泻", "拉肚子", "水样便", "拉稀", "便秘", "黑便", "便血", "大便", "拉屎"), "negative"),
    "sleep": ("睡眠", ("睡不着", "失眠", "夜醒", "醒了", "没睡好", "入睡困难", "睡不踏实", "半醒半睡"), "negative"),
    "weight": ("体重", ("体重", "长胖", "变瘦", "瘦了"), "neutral"),
    "mood": ("情绪", ("焦虑", "抑郁", "不开心", "烦躁", "情绪差", "胡思乱想", "思虑过重"), "negative"),
    "food": ("饮食", ("早餐", "午餐", "晚餐", "吃了", "吃饭", "喝了"), "neutral"),
    "exercise": ("运动", ("散步", "爬山", "运动", "锻炼", "走路", "站桩"), "positive"),
    "medication_response": ("用药反应", ("中药", "喝药", "吃药", "服药", "益生菌", "焦虑药", "蒙脱石散"), "neutral"),
    "blood_pressure": ("血压", (), "neutral"),
    "blood_glucose": ("血糖", (), "neutral"),
    "temperature": ("体温", ("发热", "发烧"), "negative"),
    "other_symptoms": ("其他身体表现", ("疼", "头晕", "人软", "怕冷", "口腔溃疡", "耳鸣", "目赤", "遗精"), "negative"),
}


class WesternPreventionEngine:
    ENGINE_VERSION = "western-transparent-1.0"
    RULE_SET_VERSION = "familycare-rules-1.0"

    def generate(self, db: Session, member_id: int, period_days: int, trigger_type: str = "manual", trigger_source_id: int | None = None, now_at: datetime | None = None) -> dict:
        if period_days not in (7, 30):
            raise ValueError("仅支持7天或30天分析")
        MedicalRuleService().ensure_baseline(db)
        end = (now_at or datetime.now()).replace(microsecond=0) + timedelta(seconds=1)
        current_start = end - timedelta(days=period_days)
        baseline_end = current_start
        baseline_start = baseline_end - timedelta(days=period_days)
        logs = list(db.scalars(select(HealthLog).where(
            HealthLog.member_id == member_id,
            HealthLog.occurred_at >= baseline_start,
            HealthLog.occurred_at < end,
        ).order_by(HealthLog.occurred_at)))
        measurements = list(db.scalars(select(Measurement).where(
            Measurement.member_id == member_id,
            Measurement.measured_at >= baseline_start,
            Measurement.measured_at < end,
        ).order_by(Measurement.measured_at)))

        run = HealthAnalysisRun(
            member_id=member_id, engine="western", period_days=period_days,
            current_start=current_start, current_end=end - timedelta(seconds=1),
            baseline_start=baseline_start, baseline_end=baseline_end,
            engine_version=self.ENGINE_VERSION, rule_set_version=self.RULE_SET_VERSION,
            trigger_type=trigger_type, trigger_source_id=trigger_source_id,
        )
        db.add(run)
        db.flush()

        payload_results: list[dict] = []
        for key, (label, keywords, direction) in CATEGORIES.items():
            current_logs, baseline_logs = self._category_logs(key, keywords, logs, current_start, end)
            current_measurements, baseline_measurements = self._category_measurements(key, measurements, current_start, end)
            current_items = [("log", row) for row in current_logs] + [("measurement", row) for row in current_measurements]
            baseline_items = [("log", row) for row in baseline_logs] + [("measurement", row) for row in baseline_measurements]
            current_days = len({self._item_time(kind, row).date() for kind, row in current_items})
            baseline_days = len({self._item_time(kind, row).date() for kind, row in baseline_items})
            red_assessments = [MedicalSafetyLayer().assess(row.raw_text) for row in current_logs]
            red = next((item for item in red_assessments if item.possible_emergency), None)
            trend = self._trend(current_days, baseline_days, direction, len(current_items) + len(baseline_items))
            risk_level, escalation, rule_ids = self._risk(trend, current_days, baseline_days, len(current_items) + len(baseline_items), red)
            uncertainty = self._uncertainty(key, len(current_items), len(baseline_items), trend)
            summary = self._summary(label, period_days, current_days, baseline_days, trend, risk_level, current_measurements, baseline_measurements)
            suggestion = self._suggestion(risk_level)
            result = HealthAnalysisResult(
                run_id=run.id, category=key, status="observed" if current_items else "no_current_record",
                trend=trend, risk_level=risk_level, summary=summary,
                uncertainty=json.dumps(uncertainty, ensure_ascii=False), suggestion=json.dumps(suggestion, ensure_ascii=False),
                escalation_action=escalation, rule_ids=json.dumps(rule_ids, ensure_ascii=False),
            )
            db.add(result)
            db.flush()
            evidence = self._save_evidence(db, result.id, current_items, baseline_items)
            payload_results.append(self._result_dict(result, evidence, current_days, baseline_days))

        overall = self._overall(run.id, payload_results)
        db.add(overall)
        db.commit()
        db.refresh(run)
        return self._run_dict(run, [self._result_dict(overall, [], 0, 0), *payload_results])

    def latest(self, db: Session, member_id: int, period_days: int) -> dict | None:
        run = db.scalar(select(HealthAnalysisRun).where(
            HealthAnalysisRun.member_id == member_id,
            HealthAnalysisRun.engine == "western",
            HealthAnalysisRun.period_days == period_days,
        ).order_by(desc(HealthAnalysisRun.generated_at), desc(HealthAnalysisRun.id)).limit(1))
        if not run:
            return None
        results = list(db.scalars(select(HealthAnalysisResult).where(HealthAnalysisResult.run_id == run.id).order_by(HealthAnalysisResult.id)))
        payload = []
        for result in results:
            evidence_rows = list(db.scalars(select(HealthEvidence).where(HealthEvidence.result_id == result.id).order_by(HealthEvidence.recorded_at)))
            evidence = [self._evidence_dict(x) for x in evidence_rows]
            current_days = len({x["recorded_at"].date() for x in evidence if x["recorded_at"] and x["summary"].startswith("当前周期")})
            baseline_days = len({x["recorded_at"].date() for x in evidence if x["recorded_at"] and x["summary"].startswith("上一周期")})
            payload.append(self._result_dict(result, evidence, current_days, baseline_days))
        return self._run_dict(run, payload)

    def recompute(self, db: Session, member_id: int, trigger_type: str, trigger_source_id: int | None = None) -> dict:
        return {
            "member_id": member_id,
            "trigger_type": trigger_type,
            "runs": [
                self.generate(db, member_id, 7, trigger_type, trigger_source_id),
                self.generate(db, member_id, 30, trigger_type, trigger_source_id),
            ],
        }

    @staticmethod
    def _category_logs(key: str, keywords: tuple[str, ...], logs: list[HealthLog], current_start: datetime, end: datetime) -> tuple[list[HealthLog], list[HealthLog]]:
        def relevant(row: HealthLog) -> bool:
            if key == "food" and row.log_type == "food": return True
            if key == "exercise" and row.log_type == "exercise": return True
            if key == "sleep" and row.log_type == "sleep": return any(word in row.raw_text for word in keywords)
            if key == "other_symptoms" and row.log_type == "symptom": return any(word in row.raw_text for word in keywords)
            return any(word in row.raw_text for word in keywords)
        selected = [row for row in logs if relevant(row)]
        return ([row for row in selected if current_start <= row.occurred_at < end], [row for row in selected if row.occurred_at < current_start])

    @staticmethod
    def _category_measurements(key: str, rows: list[Measurement], current_start: datetime, end: datetime) -> tuple[list[Measurement], list[Measurement]]:
        expected = {"weight": "weight", "blood_pressure": "blood_pressure", "blood_glucose": "blood_glucose", "temperature": "temperature"}.get(key)
        selected = [row for row in rows if row.type == expected] if expected else []
        return ([row for row in selected if current_start <= row.measured_at < end], [row for row in selected if row.measured_at < current_start])

    @staticmethod
    def _item_time(kind: str, row) -> datetime:
        return row.occurred_at if kind == "log" else row.measured_at

    @staticmethod
    def _trend(current_days: int, baseline_days: int, direction: str, total: int) -> str:
        if total < 2 or current_days == 0 or baseline_days == 0:
            return "unknown"
        delta = current_days - baseline_days
        if abs(delta) <= 1:
            return "stable"
        if direction == "positive":
            return "improved" if delta > 0 else "worsened"
        if direction == "negative":
            return "worsened" if delta > 0 else "improved"
        return "unknown"

    @staticmethod
    def _risk(trend: str, current_days: int, baseline_days: int, total: int, red) -> tuple[str, str, list[str]]:
        if red:
            return "red", red.escalation_action, red.rule_ids
        if total < 2 or current_days == 0 or baseline_days == 0:
            return "insufficient_data", "continue_monitoring", ["WPE-DATA-001"]
        if trend == "worsened" and current_days >= 2:
            return "yellow", "schedule_medical_review", ["WPE-TREND-001"]
        return "green", "continue_monitoring", []

    @staticmethod
    def _uncertainty(key: str, current_count: int, baseline_count: int, trend: str) -> list[str]:
        items = []
        if current_count == 0: items.append("当前周期没有该类记录")
        if baseline_count == 0: items.append("上一周期缺少可比较记录")
        if trend == "unknown": items.append("现有记录不足以形成可靠的周期趋势")
        if key in ("digestive", "bowel", "sleep", "mood", "other_symptoms"): items.append("自然语言记录只能说明状态变化，不能单独用于诊断疾病")
        return items

    @staticmethod
    def _summary(label: str, days: int, current_days: int, baseline_days: int, trend: str, risk: str, current_measurements: list[Measurement], baseline_measurements: list[Measurement]) -> str:
        trend_text = {"improved": "较上一周期减少或改善", "stable": "与上一周期接近", "worsened": "较上一周期增加", "unknown": "暂无法可靠比较"}[trend]
        measurement_text = ""
        if current_measurements:
            latest = current_measurements[-1]
            value = f"{latest.value:g}" + (f"/{latest.value2:g}" if latest.value2 is not None else "") + latest.unit
            measurement_text = f"，最新记录为 {value}"
        if risk == "insufficient_data":
            return f"{label}：最近{days}天记录覆盖不足，{trend_text}{measurement_text}。"
        return f"{label}：最近{days}天涉及 {current_days} 天，上一周期涉及 {baseline_days} 天，{trend_text}{measurement_text}。"

    @staticmethod
    def _suggestion(risk: str) -> list[str]:
        return {
            "red": ["建议及时寻求专业医疗评估；如情况危急，请联系当地急救服务。"],
            "yellow": ["继续记录具体发生时间、严重程度和影响；若持续或加重，建议安排医疗复查。"],
            "green": ["继续按当前方式观察和记录。"],
            "insufficient_data": ["继续补充该类记录，系统会在数据足够后重新比较。"],
        }[risk]

    def _save_evidence(self, db: Session, result_id: int, current_items: list, baseline_items: list) -> list[dict]:
        payload = []
        for period_label, items in (("当前周期", current_items), ("上一周期", baseline_items)):
            for kind, row in items:
                if kind == "log":
                    source_type = "user_statement" if row.source == "user_reported" else "ai_extracted"
                    evidence = HealthEvidence(
                        result_id=result_id, source_type=source_type, source_id=f"health_log:{row.id}", recorded_at=row.occurred_at,
                        original_text=row.raw_text, summary=f"{period_label} · {row.occurred_at.date().isoformat()}：{row.raw_text}",
                        confirmed_by_user=row.source == "user_reported", confidence="high" if row.source == "user_reported" else "medium",
                    )
                else:
                    value = f"{row.value:g}" + (f"/{row.value2:g}" if row.value2 is not None else "") + row.unit
                    evidence = HealthEvidence(
                        result_id=result_id, source_type="measurement", source_id=f"measurement:{row.id}", recorded_at=row.measured_at,
                        original_text=row.raw_text, summary=f"{period_label} · {row.measured_at.date().isoformat()}：{row.type} {value}",
                        confirmed_by_user=row.source == "user_reported", confidence="high",
                    )
                db.add(evidence)
                db.flush()
                payload.append(self._evidence_dict(evidence))
        return payload

    @staticmethod
    def _overall(run_id: int, results: list[dict]) -> HealthAnalysisResult:
        levels = [x["risk_level"] for x in results]
        if "red" in levels:
            risk, action, summary = "red", "seek_timely_medical_evaluation", "当前周期记录触发了需要及时处理的安全提醒。"
        elif "yellow" in levels:
            risk, action, summary = "yellow", "schedule_medical_review", "部分近期状态较上一周期增加，值得继续关注。"
        elif levels.count("green") >= 3:
            risk, action, summary = "green", "continue_monitoring", "已有部分可比较记录，暂未触发红色或黄色规则。"
        else:
            risk, action, summary = "insufficient_data", "continue_monitoring", "目前可比较的数据较少，还不足以判断整体长期趋势。"
        return HealthAnalysisResult(
            run_id=run_id, category="overall", status="summary", trend="unknown", risk_level=risk, summary=summary,
            uncertainty=json.dumps(["总体结果不等同于疾病诊断"], ensure_ascii=False), suggestion=json.dumps(WesternPreventionEngine._suggestion(risk), ensure_ascii=False),
            escalation_action=action, rule_ids="[]",
        )

    @staticmethod
    def _evidence_dict(row: HealthEvidence) -> dict:
        return {"source_type": row.source_type, "source_id": row.source_id, "recorded_at": row.recorded_at, "original_text": row.original_text, "summary": row.summary, "confirmed_by_user": row.confirmed_by_user, "confidence": row.confidence}

    @staticmethod
    def _result_dict(row: HealthAnalysisResult, evidence: list[dict], current_days: int, baseline_days: int) -> dict:
        return {
            "id": row.id, "category": row.category, "status": row.status, "trend": row.trend, "risk_level": row.risk_level,
            "summary": row.summary, "evidence": evidence, "uncertainty": json.loads(row.uncertainty), "suggestion": json.loads(row.suggestion),
            "escalation_action": row.escalation_action, "rule_ids": json.loads(row.rule_ids),
            "current_period_days_with_records": current_days, "baseline_period_days_with_records": baseline_days,
        }

    @staticmethod
    def _run_dict(run: HealthAnalysisRun, results: list[dict]) -> dict:
        return {
            "run_id": run.id, "member_id": run.member_id, "engine": run.engine, "period_days": run.period_days,
            "current_period": {"start": run.current_start, "end": run.current_end},
            "baseline_period": {"start": run.baseline_start, "end": run.baseline_end},
            "engine_version": run.engine_version, "rule_set_version": run.rule_set_version,
            "trigger_type": run.trigger_type, "generated_at": run.generated_at, "results": results,
        }
