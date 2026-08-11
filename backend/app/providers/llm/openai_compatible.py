from typing import Any

import httpx

from app.core.config import settings
from app.providers.llm.base import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    async def complete(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if not settings.llm_api_key:
            raise RuntimeError("尚未配置 LLM_API_KEY，请改用 mock 或填写 .env")
        payload: dict[str, Any] = {"model": settings.llm_model, "messages": messages, "temperature": 0.2}
        if tools:
            payload["tools"] = tools
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(f"{settings.llm_base_url.rstrip('/')}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            message = response.json()["choices"][0]["message"]
            return {"content": message.get("content") or "", "tool_calls": message.get("tool_calls", [])}

