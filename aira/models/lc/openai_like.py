from __future__ import annotations

import os
from typing import Any, Iterable

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from aira.core.http import post_json


def _to_openai_messages(messages: Iterable[BaseMessage]) -> list[dict[str, Any]]:
    oa_msgs: list[dict[str, Any]] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            oa_msgs.append({"role": "user", "content": m.content})
        elif isinstance(m, SystemMessage):
            oa_msgs.append({"role": "system", "content": m.content})
        elif isinstance(m, AIMessage):
            oa_msgs.append({"role": "assistant", "content": m.content})
        else:
            oa_msgs.append({"role": "user", "content": str(m.content)})
    return oa_msgs


class OpenAICompatibleChat(BaseChatModel):
    """OpenAI Chat Completions 兼容 ChatModel（可用于 openai 与 vllm）。"""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        model: str,
        timeout: int = 60,
    ) -> None:
        super().__init__()
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key or ""
        self._model = model
        self._timeout = timeout

    @property
    def _llm_type(self) -> str:  # noqa: D401
        return "openai_compatible"

    async def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        body = {
            "model": kwargs.get("model", self._model),
            "messages": _to_openai_messages(messages),
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 512),
            "stream": False,
            "stop": stop or None,
        }
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        data = await post_json(f"{self._base_url}/chat/completions", headers=headers, json=body, timeout=self._timeout)
        text: str = data["choices"][0]["message"]["content"]
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])


class OllamaChat(BaseChatModel):
    """Ollama ChatModel，使用 /api/generate 简化实现。"""

    def __init__(self, *, base_url: str, model: str, timeout: int = 60) -> None:
        super().__init__()
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    @property
    def _llm_type(self) -> str:  # noqa: D401
        return "ollama"

    async def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        # 将历史拼成单个 prompt（简单实现）
        prompt = "\n".join(m.content for m in messages if isinstance(m, (HumanMessage, SystemMessage, AIMessage)))
        body = {"model": kwargs.get("model", self._model), "prompt": prompt, "stream": False}
        data = await post_json(f"{self._base_url}/api/generate", json=body, timeout=self._timeout)
        text: str = data.get("response", "")
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])


