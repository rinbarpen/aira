from __future__ import annotations

import pytest

from aira.models.gateway import ModelGateway, SimpleCompletionResult


class DummyAdapter:
    name = "dummy:model"

    async def generate(self, prompt: str, **kwargs):
        return SimpleCompletionResult(text=prompt.upper(), usage={"input_tokens": 1, "output_tokens": 1})

    async def count_tokens(self, text: str) -> int:
        return len(text)


@pytest.mark.asyncio
async def test_gateway_generate() -> None:
    gateway = ModelGateway()
    gateway.register(DummyAdapter())
    result = await gateway.generate("dummy:model", "hello")
    assert result.text == "HELLO"

