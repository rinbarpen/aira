"""Anthropic Claude 模型适配器。"""

from __future__ import annotations

import os
from typing import Any, List, Dict

from aira.core.http import post_json
from aira.core.tokenizer import count_tokens
from aira.models.gateway import ModelAdapter, SimpleCompletionResult


def _convert_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    converted: List[Dict[str, Any]] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if isinstance(content, str):
            converted.append({"role": role, "content": [{"type": "text", "text": content}]})
        else:
            # 对象形式时直接透传
            converted.append({"role": role, "content": content})
    return converted


class AnthropicAdapter(ModelAdapter):
    name = "claude"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        api_version: str | None = None,
    ) -> None:
        self._base_url = base_url or os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._api_version = api_version or os.environ.get("ANTHROPIC_VERSION", "2023-06-01")

    async def generate(self, prompt: str, **kwargs: Any) -> SimpleCompletionResult:
        if not self._api_key:
            raise RuntimeError("ANTHROPIC_API_KEY 未配置")
        
        model = kwargs.get("model", os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620"))
        max_tokens = kwargs.get("max_tokens", 1024)
        temperature = kwargs.get("temperature", 0.7)
        messages = kwargs.get("messages") or [
            {"role": "user", "content": prompt},
        ]
        system_prompt = kwargs.get("system")

        payload: Dict[str, Any] = {
            "model": model,
            "messages": _convert_messages(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": self._api_version,
            "content-type": "application/json",
        }
        data = await post_json(f"{self._base_url}/v1/messages", headers=headers, json=payload, timeout=60)
        text = "".join(part.get("text", "") for part in data.get("content", []) if part.get("type") == "text")
        usage = data.get("usage", {})
        if usage:
            tokens_in = usage.get("input_tokens", 0)
            tokens_out = usage.get("output_tokens", 0)
        else:
            tokens_in = count_tokens("\n".join(str(m.get("content", "")) for m in messages), model)
            tokens_out = count_tokens(text, model)
        return SimpleCompletionResult(text=text, usage={"input_tokens": tokens_in, "output_tokens": tokens_out})

    async def count_tokens(self, text: str) -> int:
        return count_tokens(text)
