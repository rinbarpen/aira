from __future__ import annotations

import pytest

from typing import Any

from aira.models.cot_embedding import CoTEmbeddingWrapper, CoTGeneratorOptions
from aira.models.gateway import ModelAdapter, SimpleCompletionResult


class DummyGeneratorAdapter(ModelAdapter):
    name = "generator"

    def __init__(self) -> None:
        self.called_with: dict[str, Any] | None = None

    async def generate(self, prompt: str, **kwargs):  # type: ignore[override]
        self.called_with = {"prompt": prompt, **kwargs}
        return SimpleCompletionResult(
            text="1. step one\n2. step two",
            usage={"input_tokens": 10, "output_tokens": 20},
        )

    async def count_tokens(self, text: str) -> int:  # type: ignore[override]
        return len(text)


class DummyTargetAdapter(ModelAdapter):
    name = "target"

    def __init__(self) -> None:
        self.received_messages: list[dict[str, str]] | None = None

    async def generate(self, prompt: str, **kwargs):  # type: ignore[override]
        self.received_messages = kwargs.get("messages", [])
        return SimpleCompletionResult(text="final answer", usage={"input_tokens": 5, "output_tokens": 6})

    async def count_tokens(self, text: str) -> int:  # type: ignore[override]
        return len(text)


@pytest.mark.asyncio
async def test_cot_embedding_injects_reasoning() -> None:
    generator = DummyGeneratorAdapter()
    target = DummyTargetAdapter()

    wrapper = CoTEmbeddingWrapper(
        target,
        generator,
        generator_options=CoTGeneratorOptions(model="deepseek-reasoner", max_tokens=512),
        show_reasoning=True,
    )

    result = await wrapper.generate("原始问题", messages=[{"role": "user", "content": "原始问题"}])

    assert generator.called_with is not None
    assert generator.called_with["model"] == "deepseek-reasoner"
    assert target.received_messages is not None
    assert target.received_messages[0]["role"] == "system"
    assert "外部推理链" in target.received_messages[0]["content"]
    assert "final answer" in result.text
    assert "外部思维链" in result.text

