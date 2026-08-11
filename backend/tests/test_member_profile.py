import json

from app.api.members import update_member, update_profile
from app.schemas.common import MemberUpdate, ProfileUpdate
from app.services.context_builder import ContextBuilder


def test_member_and_extended_profile_can_be_updated(db):
    member = update_member(1, MemberUpdate(name="测试本人", gender="男", relationship="本人"), db)
    assert member.name == "测试本人"

    profile = update_profile(
        ProfileUpdate(
            profile_version="V1.0",
            occupation="测试职业",
            profile_data={"care_priorities": ["睡眠管理"]},
            raw_profile_text="测试原始档案",
        ),
        1,
        True,
        db,
    )
    assert json.loads(profile.profile_data)["care_priorities"] == ["睡眠管理"]

    context = ContextBuilder().build(db, 1)
    assert context["profile"]["structured"]["care_priorities"] == ["睡眠管理"]
