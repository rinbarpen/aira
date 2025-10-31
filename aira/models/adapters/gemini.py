"""Gemini 模型适配器。"""

from __future__ import annotations

import os
from typing import Any

from aira.core.http import post_json
from aira.core.tokenizer import count_tokens
from aira.models.gateway import ModelAdapter, SimpleCompletionResult


class GeminiAdapter(ModelAdapter):
    name = "gemini"

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self._base_url = base_url or "https://generativelanguage.googleapis.com/v1beta"
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")

    async def generate(self, prompt: str, **kwargs: Any) -> SimpleCompletionResult:
        if not self._api_key:
            raise RuntimeError("GEMINI_API_KEY 未设置，无法调用 Gemini 接口")
        
        model = kwargs.get("model", os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))
        messages = kwargs.get("messages") or [{"role": "user", "content": prompt}]
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            text = msg.get("content", "")
            contents.append({"role": role, "parts": [{"text": text}]})

        body = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "maxOutputTokens": kwargs.get("max_tokens", 2048),
            },
        }
        url = f"{self._base_url}/models/{model}:generateContent?key={self._api_key}"
        data = await post_json(url, json=body, timeout=60)
        candidates = data.get("candidates", [])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in parts)
        usage = data.get("usageMetadata", {})
        if usage:
            tokens_in = usage.get("promptTokenCount", 0)
            tokens_out = usage.get("candidatesTokenCount", 0)
        else:
            tokens_in = count_tokens("\n".join(m.get("content", "") for m in messages), model)
            tokens_out = count_tokens(text, model)
        return SimpleCompletionResult(text=text, usage={"input_tokens": tokens_in, "output_tokens": tokens_out})

    async def count_tokens(self, text: str) -> int:
        return count_tokens(text)
