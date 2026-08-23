from app.services.medical_knowledge import MedicalKnowledgeService


def test_diabetes_knowledge_is_traceable_and_quarantined_from_analysis():
    payload = MedicalKnowledgeService().list_items("糖尿病")
    assert payload["total"] >= 6
    assert payload["enabled_for_analysis"] == 0
    assert payload["pending_review"] == payload["total"]
    for item in payload["items"]:
        assert item["id"].startswith("WM-DM-")
        assert item["sources"]
        assert all(source["publisher"] and source["url"].startswith("https://") for source in item["sources"])


def test_unknown_topic_returns_empty_result_without_inventing_knowledge():
    payload = MedicalKnowledgeService().list_items("不存在的主题")
    assert payload["total"] == 0
    assert payload["items"] == []
