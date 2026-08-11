from app.providers.feishu import FeishuOpenAPIProvider, MockFeishuProvider


def test_feishu_mock_sync_does_not_upload_files():
    result = MockFeishuProvider().sync({"members": [{"id": 1}], "documents": [{"file_name": "demo.pdf", "summary": "演示"}]})
    assert result["provider"] == "mock"
    assert "未向第三方上传任何医疗文件" in result["message"]
    assert "检查资料索引" in result["tables"]


def test_real_feishu_mapping_preserves_precise_doctor_source_and_no_file_path():
    mappings = FeishuOpenAPIProvider.build_mappings({
        "visits": [{"id": 2, "member_id": 4, "status": "FOLLOW_UP", "feedback_source": "doctor_reported_by_patient"}],
        "documents": [{"id": 3, "member_id": 4, "file_name": "demo.pdf", "file_path": "private/path/demo.pdf", "source": "uploaded_document"}],
    })
    visit = mappings["就医记录"][1][0]
    document = mappings["检查资料索引"][1][0]
    assert visit["反馈来源原值"] == "doctor_reported_by_patient"
    assert visit["反馈来源"] == "doctor_reported"
    assert "file_path" not in document
    assert document["原文件仅本地保存"] is True
