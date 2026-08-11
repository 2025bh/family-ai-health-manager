from app.services.health_parser import HealthLogParser


def test_nocturnal_emission_aliases_are_normalized_without_losing_raw_context():
    parser = HealthLogParser()

    for text in ("昨晚睡觉时射了", "半夜无意识射精", "睡醒发现遗精了"):
        parsed = parser.parse(text)
        assert parsed.structured_data["sexual_health"] == "睡眠中遗精"
        assert "睡眠中遗精" in parsed.structured_data["normalized_symptoms"]
        assert parsed.structured_data["description"] == text
