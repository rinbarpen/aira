"""统一模型网关接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol

from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential


class CompletionResult(Protocol):
    text: str
    usage: dict[str, Any]


class ModelAdapter(ABC):
    name: str

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> CompletionResult:
        raise NotImplementedError

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        raise NotImplementedError


class ModelGateway:
    """路由到具体模型适配器。"""

    def __init__(self) -> None:
        self._adapters: dict[str, ModelAdapter] = {}
        self._aliases: dict[str, str] = {}

    def register(self, adapter: ModelAdapter, aliases: list[str] | None = None) -> None:
        self._adapters[adapter.name] = adapter
        for alias in aliases or []:
            self._aliases[alias] = adapter.name

    def get(self, name: str) -> ModelAdapter:
        # 1. 直接匹配适配器名
        if name in self._adapters:
            return self._adapters[name]
        
        # 2. 匹配别名
        if name in self._aliases:
            return self._adapters[self._aliases[name]]
        
        # 3. 提取前缀并匹配（如 "openai:gpt-4" -> "openai"）
        if ":" in name:
            prefix = name.split(":", 1)[0] + ":"
            # 先检查前缀是否是别名
            if prefix in self._aliases:
                return self._adapters[self._aliases[prefix]]
            # 再检查去掉冒号的前缀
            prefix_without_colon = name.split(":", 1)[0]
            if prefix_without_colon in self._adapters:
                return self._adapters[prefix_without_colon]
        
        raise KeyError(f"Unknown model adapter: {name}")

    async def generate(self, name: str, prompt: str, **kwargs: Any) -> CompletionResult:
        adapter = self.get(name)
        async for attempt in AsyncRetrying(
            reraise=True,
            stop=stop_after_attempt(3),
            wait=wait_exponential(min=1, max=8),
            retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        ):
            with attempt:
                return await adapter.generate(prompt, **kwargs)

    async def count_tokens(self, name: str, text: str) -> int:
        adapter = self.get(name)
        return await adapter.count_tokens(text)


@dataclass
class SimpleCompletionResult:
    text: str
    usage: dict[str, Any]

