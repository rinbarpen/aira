"""Ollama 适配器（/api/generate）。"""

from __future__ import annotations

import os
from typing import Any

from aira.models.gateway import ModelAdapter, SimpleCompletionResult
from aira.core.http import post_json
from aira.core.tokenizer import count_tokens


class OllamaAdapter(ModelAdapter):
    name = "ollama"

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

    async def generate(self, prompt: str, **kwargs: Any) -> SimpleCompletionResult:
        model = kwargs.get("model", os.environ.get("OLLAMA_MODEL", "qwen2.5"))
        body = {"model": model, "prompt": prompt, "stream": False}
        data = await post_json(f"{self._base_url}/api/generate", json=body, timeout=60)
        text = data.get("response", "")
        usage = {
            "input_tokens": count_tokens(prompt, model),
            "output_tokens": count_tokens(text, model),
        }
        return SimpleCompletionResult(text=text, usage=usage)

    async def count_tokens(self, text: str) -> int:
        return count_tokens(text)


