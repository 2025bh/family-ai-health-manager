import pytest
from sqlalchemy import func, select

from app.models.entities import HealthLog
from app.services.familycare_agent import FamilyCareAgent
from app.services.medical_safety import MedicalSafetyLayer


@pytest.mark.parametrize(
    ("text", "expected_emergency", "expected_status"),
    [
        ("今天精神不错。", False, "no_red_flag"),
        ("今天突然出现黑便。", True, "current_red_flag"),
        ("今天没有黑便。", False, "negated"),
        ("没有黑便，也没有便血。", False, "negated"),
        ("去年有过一次黑便。", False, "historical"),
        ("我爸爸今天黑便。", False, "other"),
        ("如果以后出现黑便怎么办？", False, "hypothetical"),
        ("前两天腹泻，现在好了。", False, "recovered"),
        ("之前黑便，现在已经没有了。", False, "recovered"),
        ("没有黑便，但是今天出现便血。", True, "current_red_flag"),
        ("最近好像不太舒服。", False, "insufficient_context"),
        ("之前有过。", False, "insufficient_context"),
        ("家里有人最近胃疼。", False, "insufficient_context"),
        ("上午没有腹泻，下午拉了两次。", False, "conflicting_current_statements"),
        ("今天突然黒便。", True, "current_red_flag"),
        ("今天肚子有点不得劲。", False, "insufficient_context"),
        ("黑便是不是很严重？", False, "question"),
        ("医生说目前没有发现便血。", False, "negated"),
        ("2026年6月12日，今天拉了黑便。", True, "current_red_flag"),
    ],
)
def test_medical_safety_semantics(text, expected_emergency, expected_status):
    result = MedicalSafetyLayer().assess(text)
    assert result.possible_emergency is expected_emergency
    assert result.status == expected_status


def test_other_person_is_not_recorded_as_current_member_risk():
    result = MedicalSafetyLayer().assess("我爸爸今天黑便。")
    assert result.subject == "other"
    assert result.risk_level == "insufficient_data"


def test_current_red_flag_has_rule_controlled_escalation():
    result = MedicalSafetyLayer().assess("今天突然出现黑便。")
    assert result.risk_level == "red"
    assert result.escalation_action == "seek_timely_medical_evaluation"
    assert result.rule_ids == ["MSL-BLEEDING-001"]


def test_agent_does_not_write_other_person_symptom_to_current_member(db):
    before = db.scalar(select(func.count()).select_from(HealthLog).where(HealthLog.member_id == 1))
    response = FamilyCareAgent().handle(db, 1, "我爸爸今天黑便。", "other-person-case")
    after = db.scalar(select(func.count()).select_from(HealthLog).where(HealthLog.member_id == 1))
    assert response.intent == "SUBJECT_CLARIFICATION"
    assert after == before


@pytest.mark.parametrize("text", ["如果以后出现黑便怎么办？", "黑便是不是很严重？"])
def test_agent_does_not_write_hypothetical_or_question_as_current_symptom(db, text):
    before = db.scalar(select(func.count()).select_from(HealthLog).where(HealthLog.member_id == 1))
    response = FamilyCareAgent().handle(db, 1, text, f"question-{len(text)}")
    after = db.scalar(select(func.count()).select_from(HealthLog).where(HealthLog.member_id == 1))
    assert response.intent == "HEALTH_QUESTION"
    assert after == before
