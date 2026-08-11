from datetime import datetime, timedelta
import json

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.api.health_guard import create_prevention_item
from app.api.health_logs import update_log
from app.models.entities import HealthAnalysisRun, HealthEvidence, HealthLog, HealthLogRevision, MemberHealthSetting
from app.schemas.common import HealthLogUpdate
from app.schemas.health_guard import PreventionItemCreate
from app.services.health_settings import HealthSettingService
from app.services.western_prevention import WesternPreventionEngine


def test_member_health_settings_default_and_consent(db):
    service = HealthSettingService()
    setting = service.get_or_create(db, 1)
    assert setting.western_prevention_enabled is True
    assert setting.tcm_health_enabled is False
    with pytest.raises(PermissionError):
        service.update(db, 1, {"tcm_health_enabled": True, "tcm_consent_confirmed": False})
    enabled = service.update(db, 1, {"tcm_health_enabled": True, "tcm_consent_confirmed": True})
    assert enabled.tcm_health_enabled is True
    assert enabled.tcm_consent_version == "tcm-consent-v1"
    assert db.scalar(select(MemberHealthSetting).where(MemberHealthSetting.member_id == 1)) is not None


def test_western_engine_compares_current_and_previous_period_with_evidence(db):
    now = datetime(2026, 8, 11, 12, 0)
    rows = [
        HealthLog(member_id=1, log_type="sleep", raw_text="昨晚睡不着。", structured_data="{}", occurred_at=now - timedelta(days=2)),
        HealthLog(member_id=1, log_type="sleep", raw_text="昨晚又夜醒。", structured_data="{}", occurred_at=now - timedelta(days=3)),
        HealthLog(member_id=1, log_type="sleep", raw_text="入睡困难。", structured_data="{}", occurred_at=now - timedelta(days=4)),
        HealthLog(member_id=1, log_type="sleep", raw_text="上周睡不着。", structured_data="{}", occurred_at=now - timedelta(days=10)),
    ]
    db.add_all(rows)
    db.commit()
    analysis = WesternPreventionEngine().generate(db, 1, 7, now_at=now)
    sleep = next(item for item in analysis["results"] if item["category"] == "sleep")
    assert sleep["trend"] == "worsened"
    assert sleep["risk_level"] == "yellow"
    assert sleep["current_period_days_with_records"] == 3
    assert sleep["baseline_period_days_with_records"] == 1
    assert any(item["source_type"] == "user_statement" for item in sleep["evidence"])
    assert db.scalar(select(HealthEvidence)) is not None
    latest = WesternPreventionEngine().latest(db, 1, 7)
    latest_sleep = next(item for item in latest["results"] if item["category"] == "sleep")
    assert latest_sleep["current_period_days_with_records"] == sleep["current_period_days_with_records"]
    assert latest_sleep["baseline_period_days_with_records"] == sleep["baseline_period_days_with_records"]


def test_one_day_does_not_get_forced_to_green(db):
    now = datetime(2026, 8, 11, 12, 0)
    db.add(HealthLog(member_id=1, log_type="symptom", raw_text="今天有点胃胀。", structured_data="{}", occurred_at=now - timedelta(hours=1)))
    db.commit()
    analysis = WesternPreventionEngine().generate(db, 1, 7, now_at=now)
    digestive = next(item for item in analysis["results"] if item["category"] == "digestive")
    assert digestive["risk_level"] == "insufficient_data"
    assert digestive["trend"] == "unknown"


def test_current_red_flag_overrides_missing_trend_data(db):
    now = datetime(2026, 8, 11, 12, 0)
    db.add(HealthLog(member_id=1, log_type="symptom", raw_text="今天突然出现黑便。", structured_data="{}", possible_emergency=True, occurred_at=now - timedelta(hours=1)))
    db.commit()
    analysis = WesternPreventionEngine().generate(db, 1, 7, now_at=now)
    bowel = next(item for item in analysis["results"] if item["category"] == "bowel")
    assert bowel["risk_level"] == "red"
    assert bowel["escalation_action"] == "seek_timely_medical_evaluation"


def test_health_log_correction_keeps_revision_and_recomputes_both_periods(db):
    row = HealthLog(member_id=1, log_type="symptom", raw_text="今天出现黑便", structured_data=json.dumps({"description": "今天出现黑便"}, ensure_ascii=False), possible_emergency=True)
    db.add(row)
    db.commit()
    result = update_log(row.id, HealthLogUpdate(raw_text="今天没有黑便。"), db)
    revision = db.scalar(select(HealthLogRevision).where(HealthLogRevision.health_log_id == row.id))
    assert revision is not None
    assert revision.previous_raw_text == "今天出现黑便"
    assert result["possible_emergency"] is False
    assert result["recomputed_periods"] == [7, 30]
    assert len(list(db.scalars(select(HealthAnalysisRun).where(HealthAnalysisRun.trigger_type == "health_log_corrected")))) == 2


def test_prevention_item_rejects_untraceable_ai_source(db):
    payload = PreventionItemCreate(member_id=1, title="自行筛查", category="screening", reason="无来源", source_type="ai_generated")
    with pytest.raises(HTTPException) as exc:
        create_prevention_item(payload, db)
    assert exc.value.status_code == 400
