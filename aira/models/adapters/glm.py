"""ChatGLM / GLM 模型适配器。"""

from __future__ import annotations

import os
from typing import Any

from aira.core.http import post_json
from aira.core.tokenizer import count_tokens
from aira.models.gateway import ModelAdapter, SimpleCompletionResult


class GLMAdapter(ModelAdapter):
    name = "glm"

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self._base_url = base_url or os.environ.get("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        self._api_key = api_key or os.environ.get("GLM_API_KEY", "")
        if not self._api_key:
            raise RuntimeError("GLM_API_KEY 未配置")

    async def generate(self, prompt: str, **kwargs: Any) -> SimpleCompletionResult:
        model = kwargs.get("model", os.environ.get("GLM_MODEL", "glm-4-air"))
        messages = kwargs.get("messages") or [{"role": "user", "content": prompt}]
        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
        }
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        data = await post_json(f"{self._base_url}/chat/completions", headers=headers, json=payload, timeout=60)
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        if usage:
            tokens_in = usage.get("prompt_tokens", 0)
            tokens_out = usage.get("completion_tokens", 0)
        else:
            tokens_in = count_tokens("\n".join(m["content"] for m in messages if isinstance(m.get("content"), str)), model)
            tokens_out = count_tokens(text, model)
        return SimpleCompletionResult(text=text, usage={"input_tokens": tokens_in, "output_tokens": tokens_out})

    async def count_tokens(self, text: str) -> int:
        return count_tokens(text)
