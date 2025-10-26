"""Chain-of-Thought 功能使用示例。

演示如何使用外接的 CoT 功能来增强不支持原生思维链的模型。
"""

import asyncio
import os
from typing import Any

# 确保导入路径正确
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from aira.models import build_gateway
from aira.models.adapters.qwen import QwenAdapter
from aira.models.cot_wrapper import wrap_adapter_with_cot


async def example_basic_usage():
    """示例 1: 基础使用 - 通过网关自动应用 CoT"""
    print("=" * 60)
    print("示例 1: 基础使用（自动应用 CoT）")
    print("=" * 60)

    # 构建网关（会根据配置自动包装模型）
    gateway = build_gateway()

    # 使用 Qwen 模型（如果在配置中启用了 CoT，会自动包装）
    questions = [
        "9.11 和 9.9 哪个数字更大？请详细解释。",
        "为什么天空是蓝色的？",
        "如何高效地学习一门新的编程语言？",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n问题 {i}: {question}")
        try:
            result = await gateway.generate(
                "qwen:qwen-plus",  # 假设使用 Qwen Plus
                question,
                max_tokens=1024,
            )
            print(f"\n回答:\n{result.text}")
            print(f"\nToken 使用: 输入={result.usage.get('input_tokens', 0)}, "
                  f"输出={result.usage.get('output_tokens', 0)}")
        except Exception as e:
            print(f"错误: {e}")
        print("-" * 60)


async def example_manual_wrapper():
    """示例 2: 手动包装适配器"""
    print("\n" + "=" * 60)
    print("示例 2: 手动包装适配器（显示推理过程）")
    print("=" * 60)

    # 检查是否配置了 API Key
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("⚠️  未配置 DASHSCOPE_API_KEY，跳过此示例")
        return

    # 创建原始 Qwen 适配器
    qwen = QwenAdapter()

    # 手动包装为 CoT 版本，启用推理过程显示
    qwen_cot = wrap_adapter_with_cot(
        qwen,
        show_reasoning=True,  # 显示推理过程
        enable_few_shot=True,  # 启用少样本学习
    )

    question = "递归算法的优缺点是什么？"
    print(f"\n问题: {question}")

    try:
        result = await qwen_cot.generate(question, max_tokens=1024)
        print(f"\n回答（包含推理过程）:\n{result.text}")
        print(f"\nToken 使用: 输入={result.usage.get('input_tokens', 0)}, "
              f"输出={result.usage.get('output_tokens', 0)}")
    except Exception as e:
        print(f"错误: {e}")


async def example_comparison():
    """示例 3: 对比有无 CoT 的效果"""
    print("\n" + "=" * 60)
    print("示例 3: 对比有无 CoT 的效果")
    print("=" * 60)

    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("⚠️  未配置 DASHSCOPE_API_KEY，跳过此示例")
        return

    question = "一个农夫需要把狼、羊和白菜运过河，但船一次只能带一样东西。如果留狼和羊单独在一起，狼会吃羊；如果留羊和白菜单独在一起，羊会吃白菜。农夫应该怎么做？"

    print(f"\n问题: {question}\n")

    # 不使用 CoT
    print("【不使用 CoT】")
    qwen_normal = QwenAdapter()
    try:
        result_normal = await qwen_normal.generate(question, max_tokens=512)
        print(f"回答: {result_normal.text}")
        print(f"Token: {result_normal.usage.get('output_tokens', 0)}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n" + "-" * 60 + "\n")

    # 使用 CoT
    print("【使用 CoT】")
    qwen_cot = wrap_adapter_with_cot(qwen_normal, show_reasoning=True)
    try:
        result_cot = await qwen_cot.generate(question, max_tokens=1024)
        print(f"回答: {result_cot.text}")
        print(f"Token: {result_cot.usage.get('output_tokens', 0)}")
    except Exception as e:
        print(f"错误: {e}")


async def example_complex_reasoning():
    """示例 4: 复杂推理任务"""
    print("\n" + "=" * 60)
    print("示例 4: 复杂推理任务")
    print("=" * 60)

    gateway = build_gateway()

    # 数学推理
    math_question = "如果一个圆的面积增加了 44%，它的半径增加了多少？"
    print(f"\n数学问题: {math_question}")

    try:
        result = await gateway.generate(
            "qwen:qwen-plus",
            math_question,
            max_tokens=1024,
        )
        print(f"\n回答:\n{result.text}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n" + "-" * 60)

    # 逻辑推理
    logic_question = """有 5 个房子排成一排，每个房子颜色不同，住着不同国籍的人，养不同的宠物，喝不同的饮料，抽不同的烟。已知：
1. 英国人住在红色房子里
2. 瑞典人养狗
3. 丹麦人喝茶
4. 绿色房子在白色房子左边
5. 绿色房子主人喝咖啡

请推理：谁养鱼？"""

    print(f"\n逻辑推理问题:\n{logic_question}")

    try:
        result = await gateway.generate(
            "qwen:qwen-plus",
            logic_question,
            max_tokens=2048,
        )
        print(f"\n回答:\n{result.text}")
    except Exception as e:
        print(f"错误: {e}")


async def main():
    """运行所有示例"""
    print("\n" + "🧠 " * 15)
    print("Chain-of-Thought 功能演示")
    print("🧠 " * 15 + "\n")

    # 检查配置
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("⚠️  提示: 请设置 DASHSCOPE_API_KEY 环境变量以运行 Qwen 示例")
        print("export DASHSCOPE_API_KEY='your-api-key'\n")

    try:
        # 运行示例
        await example_basic_usage()
        await example_manual_wrapper()
        await example_comparison()
        await example_complex_reasoning()

    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n\n运行出错: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

