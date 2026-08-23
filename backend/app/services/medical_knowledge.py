from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


KNOWLEDGE_FILE = Path(__file__).resolve().parents[1] / "knowledge" / "western_medicine.json"


class MedicalKnowledgeService:
    @staticmethod
    @lru_cache(maxsize=1)
    def _load() -> dict:
        return json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))

    def list_items(self, topic: str | None = None) -> dict:
        payload = self._load()
        items = payload["items"]
        if topic:
            needle = topic.strip().lower()
            items = [
                item for item in items
                if needle in item["title"].lower()
                or needle in item["category"].lower()
                or any(needle in tag.lower() for tag in item["tags"])
            ]
        return {
            "version": payload["version"],
            "updated_at": payload["updated_at"],
            "disclaimer": payload["disclaimer"],
            "total": len(items),
            "enabled_for_analysis": sum(bool(item["enabled_for_analysis"]) for item in items),
            "pending_review": sum(item["status"] == "待复核" for item in items),
            "items": items,
        }
