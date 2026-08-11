import json
from datetime import datetime

from app.models.entities import HealthLog, MedicalVisit
from app.services.doctor_mode import DoctorModeService


def test_medical_visit_creation_snapshots_known_context(db):
    visit = DoctorModeService().start(db, 4)
    assert visit.status == "PREPARING"
    assert "高血压" in (visit.medical_history_snapshot or "")
    assert visit.measurement_summary


def test_doctor_mode_session_asks_one_question_at_a_time_and_finishes(db):
    service = DoctorModeService()
    visit = service.start(db, 4)
    answers = ["原来的医生，王医生", "最近十来天头晕", "十天前", "反复波动", "起床时", "有点没精神", "近期没有调整", "为什么会头晕"]
    for index, answer in enumerate(answers):
        reply, complete = service.continue_visit(db, visit, answer)
        assert reply.count("？") <= 1
        assert complete is (index == len(answers) - 1)
    assert db.get(MedicalVisit, visit.id).status == "REVIEWING"
    confirmed = service.confirm_review(db, visit)
    assert confirmed.status == "READY"
    summary = service.summary(db, visit)
    assert summary["title"] == "原医生复诊简报"
    assert summary["main_problem"] == "最近十来天头晕"
    assert summary["questions_for_doctor"] == "为什么会头晕"


def test_doctor_mode_carries_recent_nocturnal_emission_into_review(db):
    db.add(HealthLog(member_id=4, log_type="sleep", raw_text="昨晚睡着后遗精一次", structured_data=json.dumps({"sexual_health": "睡眠中遗精"}, ensure_ascii=False), occurred_at=datetime.now()))
    db.commit()

    visit = DoctorModeService().start(db, 4)
    details = json.loads(visit.symptom_summary or "{}")

    assert details["recent_sensitive_symptoms"]
    assert "睡眠中遗精" in details["recent_sensitive_symptoms"][0]


def test_review_checklist_groups_answers_and_recent_logs(db):
    service = DoctorModeService()
    visit = service.start(db, 4)
    answers = ["原来的医生，廖伯年医生", "最近十来天头晕", "十天前", "反复波动", "起床时", "有点没精神", "近期没有调整", "为什么会头晕"]
    for answer in answers:
        service.continue_visit(db, visit, answer)
    checklist = service.review_checklist(db, visit)
    assert checklist["status"] == "REVIEWING"
    assert len(checklist["answers"]) == len(answers)
    assert checklist["known_conditions"]
    assert checklist["weekly"]["days"] == 14
    assert any(x["label"] == "睡眠" for x in checklist["weekly"]["categories"])


def test_confirm_review_requires_reviewing_status(db):
    service = DoctorModeService()
    visit = service.start(db, 4)
    try:
        service.confirm_review(db, visit)
        assert False, "PREPARING 状态不应允许直接确认"
    except ValueError:
        pass


def test_new_doctor_negation_is_not_misclassified_as_returning(db):
    service = DoctorModeService()
    visit = service.start(db, 4)
    service.continue_visit(db, visit, "不是原医生，这次换了新医生")
    details = json.loads(visit.symptom_summary or "{}")
    assert details["doctor_context_type"] == "new"
    assert service.summary(db, visit)["title"] == "新医生就诊摘要"


def test_review_answer_can_be_corrected_before_confirmation(db):
    service = DoctorModeService()
    visit = service.start(db, 4)
    answers = ["原来的医生，廖伯年", "胃胀", "两周前", "正在变好", "饭后", "没有", "第九副中药", "是否继续原方"]
    for answer in answers:
        service.continue_visit(db, visit, answer)
    service.update_review_answer(db, visit, "chief_complaint", "胃胀明显减轻，近期体重增加一两斤")
    assert visit.chief_complaint == "胃胀明显减轻，近期体重增加一两斤"
    assert service.summary(db, visit)["main_problem"] == "胃胀明显减轻，近期体重增加一两斤"
    service.confirm_review(db, visit)
    service.mark_shared_with_doctor(db, visit)
    assert visit.status == "VISITED"
