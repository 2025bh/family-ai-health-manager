from app.services.safety import SafetyService


def test_safety_service_stops_normal_chat_for_possible_emergency():
    result = SafetyService().check_input("我突然呼吸困难，喘不上气。")
    assert result.possible_emergency is True
    reply = SafetyService.emergency_reply()
    assert "专业医疗人员" in reply
    assert "诊断" not in reply


def test_digestive_bleeding_warning_phrase_is_detected():
    result = SafetyService().check_input("今天出现黑便")
    assert result.possible_emergency is True
    assert result.reason == "黑便"


def test_safety_service_does_not_flag_negated_black_stool_or_blood():
    result = SafetyService().check_input("最近两周没有黑便，也没有便血。")
    assert result.possible_emergency is False
    assert result.reason is None


def test_safety_service_still_flags_later_positive_symptom():
    result = SafetyService().check_input("前几天没有黑便，但是今天出现黑便。")
    assert result.possible_emergency is True
    assert result.reason == "黑便"
