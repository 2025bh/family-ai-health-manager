import json
from datetime import datetime, timedelta

from app.models.entities import HealthLog, Measurement
from app.services.weekly_summary import WeeklySummaryBuilder


def test_weekly_summary_groups_logs_and_measurements(db):
    now = datetime.now().replace(microsecond=0)
    db.add_all(
        [
            HealthLog(member_id=4, log_type="sleep", raw_text="昨晚睡得一般，起来两次。", structured_data=json.dumps({"night_wakings": 2}, ensure_ascii=False), occurred_at=now - timedelta(days=1)),
            HealthLog(member_id=4, log_type="symptom", raw_text="今天没有黑便，大便正常。", structured_data=json.dumps({"description": "今天没有黑便，大便正常。"}, ensure_ascii=False), occurred_at=now - timedelta(hours=2)),
            HealthLog(member_id=4, log_type="symptom", raw_text="睡着后遗精一次。", structured_data=json.dumps({"sexual_health": "睡眠中遗精"}, ensure_ascii=False), occurred_at=now - timedelta(days=3)),
            Measurement(member_id=4, type="blood_pressure", value=132, value2=82, unit="mmHg", measurement_context="resting", raw_text="血压132/82", measured_at=now - timedelta(days=2)),
        ]
    )
    db.commit()
    summary = WeeklySummaryBuilder().build(db, 4, days=7)
    by_key = {x["key"]: x for x in summary["categories"]}
    # seed 已含 2 条日志（睡眠/头晕）+ 2 条测量（血压/血糖）
    assert summary["log_count"] == 5
    assert summary["measurement_count"] == 3
    assert by_key["sleep"]["items"]
    assert by_key["digestive"]["items"]
    assert by_key["sexual_health"]["items"]
    assert any("睡着后遗精一次" in x["raw_text"] for x in by_key["sexual_health"]["items"])
    assert by_key["blood_pressure"]["items"]
    assert by_key["blood_glucose"]["items"]


def test_weekly_summary_only_counts_recent_window(db):
    now = datetime.now().replace(microsecond=0)
    db.add(HealthLog(member_id=4, log_type="other", raw_text="很久以前的记录。", structured_data="{}", occurred_at=now - timedelta(days=40)))
    db.commit()
    summary = WeeklySummaryBuilder().build(db, 4, days=7)
    # 只统计窗口内数据：seed 的 2 条日志仍在窗口内，40 天前的不计入
    assert summary["log_count"] == 2


def test_weekly_summary_uses_category_specific_excerpt_and_ignores_medication_only_mood(db):
    now = datetime.now().replace(microsecond=0)
    db.add_all([
        HealthLog(member_id=4, log_type="other", raw_text="昨晚两点才睡；中午吃饭后胃胀；下午精神还可以。", structured_data="{}", occurred_at=now),
        HealthLog(member_id=4, log_type="mood", raw_text="今天没有吃焦虑药，其他正常。", structured_data="{}", occurred_at=now),
    ])
    db.commit()
    summary = WeeklySummaryBuilder().build(db, 4, days=7)
    by_key = {x["key"]: x for x in summary["categories"]}
    sleep_item = next(x for x in by_key["sleep"]["items"] if "两点才睡" in x["raw_text"])
    digestive_item = next(x for x in by_key["digestive"]["items"] if "胃胀" in x["raw_text"])
    assert "胃胀" not in sleep_item["summary_text"]
    assert "两点才睡" not in digestive_item["summary_text"]
    assert not any("没有吃焦虑药" in x["raw_text"] for x in by_key["mood"]["items"])
