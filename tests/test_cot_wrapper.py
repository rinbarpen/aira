"""Chain-of-Thought 包装器测试。"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from aira.models.cot_wrapper import CoTWrapper, wrap_adapter_with_cot
from aira.models.gateway import SimpleCompletionResult, ModelAdapter


class MockAdapter(ModelAdapter):
    """测试用的模拟适配器。"""

    name = "mock"

    async def generate(self, prompt: str, **kwargs) -> SimpleCompletionResult:
        """模拟生成响应。"""
        # 模拟返回格式正确的 CoT 响应
        text = """<思考>
1. 这是一个测试问题
2. 需要进行逐步分析
3. 评估可能的解决方案
4. 得出结论
</思考>

<回答>
这是最终答案
</回答>"""
        return SimpleCompletionResult(
            text=text,
            usage={"input_tokens": 100, "output_tokens": 50},
        )

    async def count_tokens(self, text: str) -> int:
        """模拟 token 计数。"""
        return len(text.split())


@pytest.mark.asyncio
async def test_cot_wrapper_basic():
    """测试基本的 CoT 包装功能。"""
    mock_adapter = MockAdapter()
    cot_wrapper = CoTWrapper(mock_adapter, show_reasoning=False)

    result = await cot_wrapper.generate("测试问题")

    # 验证推理过程被正确提取，但不显示
    assert "思考" not in result.text
    assert "这是最终答案" in result.text
    assert result.usage["input_tokens"] == 100
    assert result.usage["output_tokens"] == 50


@pytest.mark.asyncio
async def test_cot_wrapper_show_reasoning():
    """测试显示推理过程的功能。"""
    mock_adapter = MockAdapter()
    cot_wrapper = CoTWrapper(mock_adapter, show_reasoning=True)

    result = await cot_wrapper.generate("测试问题")

    # 验证推理过程被显示
    assert "【思考过程】" in result.text
    assert "【最终答案】" in result.text
    assert "这是一个测试问题" in result.text
    assert "这是最终答案" in result.text


@pytest.mark.asyncio
async def test_cot_wrapper_messages():
    """测试处理消息列表的功能。"""
    mock_adapter = MockAdapter()
    cot_wrapper = CoTWrapper(mock_adapter, show_reasoning=False, enable_few_shot=False)

    messages = [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "测试问题"},
    ]

    result = await cot_wrapper.generate("", messages=messages)

    # 验证 CoT 系统提示被注入
    assert result.text
    assert isinstance(result.usage, dict)


@pytest.mark.asyncio
async def test_wrap_adapter_with_cot():
    """测试便捷包装函数。"""
    mock_adapter = MockAdapter()
    wrapped = wrap_adapter_with_cot(mock_adapter, show_reasoning=True)

    assert isinstance(wrapped, CoTWrapper)
    assert wrapped.name == "mock_cot"
    assert wrapped.show_reasoning is True


@pytest.mark.asyncio
async def test_cot_extraction_fallback():
    """测试当模型没有按格式输出时的回退机制。"""

    class BadFormatAdapter(ModelAdapter):
        name = "bad"

        async def generate(self, prompt: str, **kwargs) -> SimpleCompletionResult:
            # 返回不符合格式的响应
            return SimpleCompletionResult(
                text="这是一个没有标签的普通回答",
                usage={"input_tokens": 10, "output_tokens": 5},
            )

        async def count_tokens(self, text: str) -> int:
            return len(text.split())

    bad_adapter = BadFormatAdapter()
    cot_wrapper = CoTWrapper(bad_adapter, show_reasoning=False)

    result = await cot_wrapper.generate("测试问题")

    # 验证即使没有标签也能正常返回
    assert result.text == "这是一个没有标签的普通回答"


@pytest.mark.asyncio
async def test_token_counting():
    """测试 token 计数委托。"""
    mock_adapter = MockAdapter()
    cot_wrapper = CoTWrapper(mock_adapter)

    count = await cot_wrapper.count_tokens("测试文本 test text")
    assert count > 0

