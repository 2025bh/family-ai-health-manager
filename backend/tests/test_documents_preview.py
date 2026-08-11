from PIL import Image

from datetime import date, datetime

from app.api.documents import _display_name, _effective_document_type, _is_image, ensure_thumbnail
from app.models.entities import HealthDocument


def test_is_image():
    assert _is_image("a.png")
    assert _is_image("a.JPG")
    assert not _is_image("a.pdf")


def test_ensure_thumbnail_generates_webp(tmp_path, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    src = tmp_path / "demo.png"
    Image.new("RGB", (900, 700), "#2E7D5B").save(src)
    dst = ensure_thumbnail(src)
    assert dst is not None and dst.exists()
    with Image.open(dst) as im:
        assert im.format == "WEBP"
        assert im.width <= 420
        assert im.height <= 420


def test_ensure_thumbnail_reuses_existing(tmp_path, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    src = tmp_path / "demo.png"
    Image.new("RGB", (500, 400), "#2E7D5B").save(src)
    first = ensure_thumbnail(src)
    second = ensure_thumbnail(src)
    assert first == second
    assert second.exists()


def test_legacy_document_gets_effective_category_and_chinese_title():
    row = HealthDocument(member_id=1, document_type="other", file_name="IMG_123.jpeg", file_path="IMG_123.jpeg", document_date=date(2026, 6, 26), ai_summary="川北医学院附属医院，第六副中药处方", created_at=datetime.now())
    document_type = _effective_document_type(row)
    assert document_type == "prescription"
    assert _display_name(row, document_type) == "2026-06-26 第六副处方"


def test_historical_custom_document_types_are_normalized_for_the_ui():
    prescription = HealthDocument(member_id=1, document_type="prescription_tcm_course_5", file_name="IMG_A.jpeg", file_path="IMG_A.jpeg", document_date=date(2026, 6, 14), ai_summary="第五副中药处方", created_at=datetime.now())
    outpatient = HealthDocument(member_id=1, document_type="outpatient_record_tcm", file_name="IMG_B.jpeg", file_path="IMG_B.jpeg", document_date=date(2026, 6, 26), ai_summary="中医胃肠专科门诊病历", created_at=datetime.now())
    assert _effective_document_type(prescription) == "prescription"
    assert _display_name(prescription, "prescription") == "2026-06-14 第五副处方"
    assert _effective_document_type(outpatient) == "doctor_note"
    assert _display_name(outpatient, "doctor_note") == "2026-06-26 中医胃肠专科门诊病历"
