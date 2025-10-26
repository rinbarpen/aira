"""OpenAI 模型适配器示例。"""

from __future__ import annotations

import os
from typing import Any

import httpx

from aira.models.gateway import ModelAdapter, SimpleCompletionResult


class OpenAIAdapter(ModelAdapter):
    name = "openai:gpt-4o"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=30)
        self._base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self._api_key = os.environ.get("OPENAI_API_KEY", "")

    async def generate(self, prompt: str, **kwargs: Any) -> SimpleCompletionResult:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {
            "model": kwargs.get("model", "gpt-4o-mini"),
            "input": prompt,
            "max_output_tokens": kwargs.get("max_tokens", 1024),
        }
        response = await self._client.post(f"{self._base_url}/responses", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        text = data["output"][0]["content"][0]["text"]
        usage = data.get("usage", {})
        return SimpleCompletionResult(text=text, usage=usage)

    async def count_tokens(self, text: str) -> int:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {
            "model": "gpt-4o-mini",
            "input": text,
        }
        response = await self._client.post(f"{self._base_url}/tokenize", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return int(data.get("total_tokens", 0))

