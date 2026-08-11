from app.services.context_builder import ContextBuilder


def test_context_loading_is_scoped_and_contains_profile(db):
    context = ContextBuilder().build(db, 4, days=30)
    assert context["member"]["name"] == "爷爷"
    assert "高血压" in context["profile"]["known_conditions"]
    assert context["recent_logs"]
    assert len(context["recent_measurements"]) <= 20


def test_context_contains_extended_structured_profile(db):
    import json
    from sqlalchemy import select
    from app.models.entities import HealthProfile

    profile = db.scalar(select(HealthProfile).where(HealthProfile.member_id == 1))
    profile.profile_version = "V1.0"
    profile.occupation = "测试职业"
    profile.profile_data = json.dumps({"care_priorities": ["睡眠管理"]}, ensure_ascii=False)
    db.commit()

    context = ContextBuilder().build(db, 1)
    assert context["profile"]["profile_version"] == "V1.0"
    assert context["profile"]["occupation"] == "测试职业"
    assert context["profile"]["structured"]["care_priorities"] == ["睡眠管理"]
    assert "health_documents" in context
    assert "medication_courses" in context
