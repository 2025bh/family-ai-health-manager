from abc import ABC, abstractmethod
from datetime import datetime

import httpx

from app.core.config import settings


class FeishuProvider(ABC):
    table_names = ("家庭成员", "健康日志", "健康测量", "就医记录", "健康任务", "检查资料索引")

    @abstractmethod
    def sync(self, snapshot: dict) -> dict: ...


class MockFeishuProvider(FeishuProvider):
    """不上传原始医疗文件，只记录可核验的同步摘要。"""

    def sync(self, snapshot: dict) -> dict:
        return {
            "provider": "mock",
            "synced_at": datetime.now().isoformat(timespec="seconds"),
            "tables": list(self.table_names),
            "counts": {key: len(value) for key, value in snapshot.items() if isinstance(value, list)},
            "message": "Mock 同步成功；未向第三方上传任何医疗文件。",
        }


class FeishuOpenAPIProvider(FeishuProvider):
    """真实飞书同步：按本地业务 ID 更新或新增，避免重复记录。"""

    api_base = "https://open.feishu.cn/open-apis"

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=30)
        self.access_token = settings.feishu_user_access_token

    def _ensure_token(self) -> str:
        if self.access_token:
            return self.access_token
        if not settings.feishu_app_id or not settings.feishu_app_secret:
            raise RuntimeError("真实飞书同步需要 FEISHU_USER_ACCESS_TOKEN，或 App ID + App Secret")
        response = self.client.post(
            f"{self.api_base}/auth/v3/tenant_access_token/internal",
            json={"app_id": settings.feishu_app_id, "app_secret": settings.feishu_app_secret},
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code", 0) != 0:
            raise RuntimeError(f"获取飞书访问凭证失败：{data.get('msg')}")
        self.access_token = data["tenant_access_token"]
        return self.access_token

    def _request(self, method: str, path: str, **kwargs) -> dict:
        headers = {"Authorization": f"Bearer {self._ensure_token()}"}
        response = self.client.request(method, f"{self.api_base}{path}", headers=headers, **kwargs)
        response.raise_for_status()
        result = response.json()
        if result.get("code", 0) != 0:
            raise RuntimeError(f"飞书接口失败：{result.get('code')} {result.get('msg')}")
        return result.get("data") or {}

    def _table_ids(self) -> dict[str, str]:
        data = self._request("GET", f"/base/v3/bases/{settings.feishu_base_token}/tables", params={"limit": 50, "offset": 0})
        return {item["table_name"]: item["table_id"] for item in data.get("items", [])}

    def _existing_records(self, table_id: str) -> list[dict]:
        rows: list[dict] = []
        offset = 0
        while True:
            data = self._request("GET", f"/base/v3/bases/{settings.feishu_base_token}/tables/{table_id}/records", params={"limit": 100, "offset": offset})
            rows.extend(data.get("items", []))
            if not data.get("has_more"):
                break
            offset += len(data.get("items", []))
        return rows

    @staticmethod
    def _chunks(values: list, size: int = 200):
        for index in range(0, len(values), size):
            yield values[index:index + size]

    def _sync_table(self, table_id: str, key: str, records: list[dict]) -> dict:
        existing = {}
        for row in self._existing_records(table_id):
            value = (row.get("fields") or {}).get(key)
            if value is not None:
                existing[str(value)] = row.get("record_id")
        creates: list[dict] = []
        updates: dict[str, dict] = {}
        for record in records:
            record_id = existing.get(str(record.get(key)))
            if record_id:
                updates[record_id] = record
            else:
                creates.append(record)
        for batch in self._chunks(creates):
            self._request("POST", f"/base/v3/bases/{settings.feishu_base_token}/tables/{table_id}/records/batch_create", json={"create_records": batch})
        update_items = list(updates.items())
        for batch in self._chunks(update_items):
            self._request("POST", f"/base/v3/bases/{settings.feishu_base_token}/tables/{table_id}/records/batch_update", json={"update_records": dict(batch)})
        return {"created": len(creates), "updated": len(updates)}

    @staticmethod
    def build_mappings(snapshot: dict) -> dict[str, tuple[str, list[dict]]]:
        members = [{"Text": f"{x['name']}（FamilyCare）", "member_id": str(x["id"]), "姓名": x["name"], "关系": x.get("relationship") or "", "常用称呼": x.get("preferred_name") or x["name"]} for x in snapshot.get("members", [])]
        logs = [{"log_id": str(x["id"]), "member_id": str(x["member_id"]), "类型": x["type"], "老人原话": x["raw_text"], "结构化结果JSON": x.get("structured_data") or "{}", "来源": x.get("source", "user_reported"), "可能紧急": bool(x.get("possible_emergency")), "发生时间": x.get("occurred_at")} for x in snapshot.get("health_logs", [])]
        measurements = [{"measurement_id": str(x["id"]), "member_id": str(x["member_id"]), "类型": x["type"], "数值1": x["value"], "数值2": x.get("value2"), "单位": x["unit"], "测量场景": x.get("measurement_context", "unknown"), "原话": x.get("raw_text", ""), "来源": x.get("source", "user_reported"), "测量时间": x.get("measured_at")} for x in snapshot.get("measurements", [])]
        visits = [{"visit_id": str(x["id"]), "member_id": str(x["member_id"]), "状态": x["status"], "主要问题": x.get("chief_complaint") or "", "症状摘要JSON": x.get("symptom_summary") or "{}", "已知病史快照": x.get("medical_history_snapshot") or "", "长期用药快照": x.get("medication_snapshot") or "", "医生反馈": x.get("doctor_feedback") or "", "反馈来源": "doctor_reported" if x.get("feedback_source") == "doctor_reported_by_patient" else (x.get("feedback_source") or "user_reported"), "反馈来源原值": x.get("feedback_source") or "user_reported", "复查日期": x.get("follow_up_date")} for x in snapshot.get("visits", [])]
        tasks = [{"task_id": str(x["id"]), "member_id": str(x["member_id"]), "任务类型": x.get("task_type", "general"), "标题": x["title"], "描述": x.get("description") or "", "计划时间": x.get("scheduled_at"), "重复规则": x.get("recurrence") or "", "来源": x.get("source", "system"), "状态": x.get("status", "pending")} for x in snapshot.get("tasks", [])]
        documents = [{"document_id": str(x["id"]), "member_id": str(x["member_id"]), "资料类型": x.get("document_type", "other"), "文件名": x["file_name"], "资料日期": x.get("document_date"), "摘要": x.get("summary") or "", "来源": x.get("source", "uploaded_document"), "原文件仅本地保存": True} for x in snapshot.get("documents", [])]
        return {
            "家庭成员": ("member_id", members),
            "健康日志": ("log_id", logs),
            "健康测量": ("measurement_id", measurements),
            "就医记录": ("visit_id", visits),
            "健康任务": ("task_id", tasks),
            "检查资料索引": ("document_id", documents),
        }

    def sync(self, snapshot: dict) -> dict:
        if not settings.feishu_base_token:
            raise RuntimeError("真实飞书同步需要 FEISHU_BASE_TOKEN")
        table_ids = self._table_ids()
        missing = [name for name in self.table_names if name not in table_ids]
        if missing:
            raise RuntimeError(f"飞书缺少数据表：{', '.join(missing)}")
        result = {}
        for name, (key, records) in self.build_mappings(snapshot).items():
            result[name] = self._sync_table(table_ids[name], key, records)
        return {"provider": "feishu", "synced_at": datetime.now().isoformat(timespec="seconds"), "tables": result, "message": "飞书同步完成；原始医疗文件未上传。"}


def get_feishu_provider() -> FeishuProvider:
    return FeishuOpenAPIProvider() if settings.feishu_provider == "feishu" else MockFeishuProvider()
