"""Qwen 模型适配器。"""

from __future__ import annotations

import os
from typing import Any

from aira.core.http import post_json
from aira.core.tokenizer import count_tokens
from aira.models.gateway import ModelAdapter, SimpleCompletionResult


class QwenAdapter(ModelAdapter):
    name = "qwen"

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self._base_url = base_url or os.environ.get("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self._api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "")
        if not self._api_key:
            raise RuntimeError("DASHSCOPE_API_KEY 未配置")

    async def generate(self, prompt: str, **kwargs: Any) -> SimpleCompletionResult:
        model = kwargs.get("model", os.environ.get("QWEN_MODEL", "qwen-plus"))
        messages = kwargs.get("messages") or [{"role": "user", "content": prompt}]
        body = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
        }
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        data = await post_json(f"{self._base_url}/chat/completions", headers=headers, json=body, timeout=60)
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
