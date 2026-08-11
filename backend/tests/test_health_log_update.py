import json

from app.api.health_logs import update_log
from app.models.entities import HealthLog
from app.schemas.common import HealthLogUpdate


def test_health_log_correction_reparses_text_and_recalculates_safety(db):
    row = HealthLog(member_id=4, log_type="symptom", raw_text="今天出现黑便", structured_data=json.dumps({"description": "今天出现黑便"}, ensure_ascii=False), possible_emergency=True)
    db.add(row)
    db.commit()
    db.refresh(row)

    result = update_log(row.id, HealthLogUpdate(raw_text="最近两周没有黑便，也没有便血。"), db)

    assert result["raw_text_preserved"] == "最近两周没有黑便，也没有便血。"
    assert result["possible_emergency"] is False
    assert db.get(HealthLog, row.id).possible_emergency is False
