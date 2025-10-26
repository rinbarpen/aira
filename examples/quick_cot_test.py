#!/usr/bin/env python3
"""快速测试 CoT 功能是否正常工作。

这个脚本不需要真实的 API 密钥，使用模拟适配器来验证 CoT 包装逻辑。
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from aira.models.gateway import ModelAdapter, SimpleCompletionResult
from aira.models.cot_wrapper import CoTWrapper


class MockAdapter(ModelAdapter):
    """模拟适配器，用于测试。"""

    name = "mock"

    async def generate(self, prompt: str, **kwargs) -> SimpleCompletionResult:
        """返回模拟的 CoT 格式响应。"""
        # 检查是否被 CoT 包装器调用
        messages = kwargs.get("messages", [])
        
        has_cot_prompt = any(
            "<思考>" in msg.get("content", "") or "思考>" in msg.get("content", "")
            for msg in messages
        )
        
        if has_cot_prompt:
            # 返回符合 CoT 格式的响应
            text = """<思考>
1. 收到了包含 CoT 提示的消息
2. 提示中要求使用 <思考> 和 <回答> 标签
3. 我会按照要求的格式回复
4. 这样可以让包装器正确提取内容
</思考>

<回答>
CoT 包装器工作正常！提示已正确注入，响应格式符合预期。
</回答>"""
        else:
            # 普通响应
            text = "这是一个普通的响应，没有使用 CoT 格式。"
        
        return SimpleCompletionResult(
            text=text,
            usage={"input_tokens": 100, "output_tokens": 50}
        )

    async def count_tokens(self, text: str) -> int:
        """简单的 token 计数。"""
        return len(text.split())


async def test_cot_wrapper():
    """测试 CoT 包装器。"""
    print("🧪 Chain-of-Thought 包装器测试")
    print("=" * 60)
    
    # 创建模拟适配器
    mock = MockAdapter()
    
    # 测试 1: 不使用 CoT
    print("\n【测试 1】直接调用（不使用 CoT）")
    result = await mock.generate("测试问题")
    print(f"响应: {result.text}")
    assert "普通" in result.text
    print("✅ 通过")
    
    # 测试 2: 使用 CoT，不显示推理
    print("\n【测试 2】使用 CoT，隐藏推理过程")
    cot_wrapper = CoTWrapper(mock, show_reasoning=False)
    result = await cot_wrapper.generate("测试问题")
    print(f"响应: {result.text}")
    assert "CoT 包装器工作正常" in result.text
    assert "【思考过程】" not in result.text  # 不应显示推理标记
    print("✅ 通过")
    
    # 测试 3: 使用 CoT，显示推理
    print("\n【测试 3】使用 CoT，显示推理过程")
    cot_wrapper_with_reasoning = CoTWrapper(mock, show_reasoning=True)
    result = await cot_wrapper_with_reasoning.generate("测试问题")
    print(f"响应:\n{result.text}")
    assert "【思考过程】" in result.text
    assert "【最终答案】" in result.text
    assert "包装器工作正常" in result.text
    print("✅ 通过")
    
    # 测试 4: 检查提示注入
    print("\n【测试 4】验证 CoT 提示注入")
    cot_wrapper = CoTWrapper(mock, enable_few_shot=False)
    
    # 查看注入的消息
    test_messages = cot_wrapper._inject_cot_prompt("测试", None)
    has_system = any(msg["role"] == "system" for msg in test_messages)
    has_cot_keywords = any(
        "<思考>" in msg.get("content", "") 
        for msg in test_messages
    )
    
    assert has_system, "应该包含系统提示"
    assert has_cot_keywords, "应该包含 CoT 关键词"
    print(f"✅ 系统提示已注入")
    print(f"✅ CoT 格式要求已包含")
    
    # 测试 5: 少样本学习
    print("\n【测试 5】验证少样本学习示例")
    cot_wrapper_few_shot = CoTWrapper(mock, enable_few_shot=True)
    test_messages = cot_wrapper_few_shot._inject_cot_prompt("测试", None)
    
    # 检查是否包含示例
    message_count = len(test_messages)
    print(f"消息数量: {message_count}")
    assert message_count > 2, "启用少样本时应包含示例"
    print("✅ 少样本示例已包含")
    
    # 测试 6: Token 计数
    print("\n【测试 6】Token 计数委托")
    count = await cot_wrapper.count_tokens("测试文本")
    assert count > 0
    print(f"Token 计数: {count}")
    print("✅ 通过")
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过！CoT 功能运行正常。")
    print("=" * 60)


async def test_extraction():
    """测试答案提取逻辑。"""
    print("\n\n🔍 答案提取测试")
    print("=" * 60)
    
    mock = MockAdapter()
    cot = CoTWrapper(mock)
    
    # 测试情况 1: 标准格式
    print("\n【情况 1】标准 <思考> <回答> 格式")
    text1 = """<思考>
这是推理过程
</思考>

<回答>
这是答案
</回答>"""
    reasoning, answer = cot._extract_answer(text1)
    assert "推理过程" in reasoning
    assert "这是答案" in answer
    print(f"推理: {reasoning}")
    print(f"答案: {answer}")
    print("✅ 通过")
    
    # 测试情况 2: 无标签格式
    print("\n【情况 2】无标签格式（回退机制）")
    text2 = "这是一个没有标签的普通回答"
    reasoning, answer = cot._extract_answer(text2)
    assert answer == text2
    print(f"答案: {answer}")
    print("✅ 通过（正确回退）")
    
    # 测试情况 3: 不完整格式
    print("\n【情况 3】只有思考，没有回答")
    text3 = """<思考>
只有思考内容
</思考>"""
    reasoning, answer = cot._extract_answer(text3)
    print(f"推理: {reasoning}")
    print(f"答案: {answer}")
    print("✅ 通过（正确处理）")
    
    print("\n" + "=" * 60)
    print("🎉 提取逻辑测试通过！")
    print("=" * 60)


async def main():
    """运行所有测试。"""
    try:
        await test_cot_wrapper()
        await test_extraction()
        print("\n✨ 所有功能验证完成！CoT 功能可以正常使用。")
        return 0
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

