from __future__ import annotations

import pytest

from aira.models import build_gateway


@pytest.mark.asyncio
async def test_gateway_has_adapters() -> None:
    gateway = build_gateway()
    # 验证主要前缀都存在
    assert gateway.get("openai")
    assert gateway.get("vllm")
    assert gateway.get("ollama")
    assert gateway.get("hf")
    assert gateway.get("gemini")
    assert gateway.get("claude")
    assert gateway.get("qwen")
    assert gateway.get("kimi")
    assert gateway.get("glm")
    assert gateway.get("deepseek")

