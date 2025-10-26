"""OpenAI Chat Completions 兼容适配器。

支持标准 OpenAI /v1/chat/completions 以及兼容此协议的服务（含 vLLM）。
"""

from __future__ import annotations

import os
from typing import Any

from aira.models.gateway import ModelAdapter, SimpleCompletionResult
from aira.core.http import post_json
from aira.core.tokenizer import count_tokens


class OpenAIChatAdapter(ModelAdapter):
    name = "openai"

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self._base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    async def generate(self, prompt: str, **kwargs: Any) -> SimpleCompletionResult:
        model = kwargs.get("model", os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))
        messages = kwargs.get("messages") or [
            {"role": "user", "content": prompt},
        ]
        body = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 512),
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        data = await post_json(f"{self._base_url}/chat/completions", headers=headers, json=body, timeout=60)
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        if not usage:
            usage = {
                "input_tokens": count_tokens("\n".join(m["content"] for m in messages), model),
                "output_tokens": count_tokens(text, model),
            }
        return SimpleCompletionResult(text=text, usage=usage)

    async def count_tokens(self, text: str) -> int:
        return count_tokens(text)

