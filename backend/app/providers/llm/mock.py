from typing import Any

from app.providers.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    async def complete(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {"content": "我听到了。你愿意再多说一点吗？", "tool_calls": []}

