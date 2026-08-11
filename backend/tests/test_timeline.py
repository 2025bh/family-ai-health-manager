from app.services.timeline import build_timeline


def test_timeline_combines_long_term_events_in_reverse_order(db):
    rows = build_timeline(db, 4)
    kinds = {row["kind"] for row in rows}
    assert {"health_log", "measurement", "medical_visit", "care_task"}.issubset(kinds)
    assert rows == sorted(rows, key=lambda x: x["time"], reverse=True)

