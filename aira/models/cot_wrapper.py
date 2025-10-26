"""Chain-of-Thought 包装器。

为不支持原生思维链的模型提供外接的思维链功能。
通过提示工程引导模型进行逐步推理。
"""

from __future__ import annotations

import re
from typing import Any

from aira.models.gateway import ModelAdapter, SimpleCompletionResult


class CoTWrapper(ModelAdapter):
    """Chain-of-Thought 包装器，包装任何模型适配器以提供思维链能力。"""

    # CoT 提示模板
    COT_SYSTEM_PROMPT = """你是一个善于思考的AI助手。在回答问题时，请遵循以下格式：

<思考>
在这里进行逐步分析和推理：
1. 理解问题的核心是什么
2. 分解问题的关键要素
3. 逐步推导可能的解决方案
4. 评估不同方案的优劣
5. 得出最终结论
</思考>

<回答>
在这里给出最终的简洁回答
</回答>

请务必按照上述格式回答所有问题。"""

    COT_USER_TEMPLATE = """请对以下问题进行深入思考并回答：

{original_prompt}

请先在<思考>标签中展示你的推理过程，然后在<回答>标签中给出最终答案。"""

    def __init__(
        self,
        wrapped_adapter: ModelAdapter,
        show_reasoning: bool = False,
        enable_few_shot: bool = True,
    ) -> None:
        """初始化 CoT 包装器。

        Args:
            wrapped_adapter: 要包装的模型适配器
            show_reasoning: 是否在最终结果中显示推理过程（默认不显示）
            enable_few_shot: 是否启用少样本示例（帮助模型更好理解格式）
        """
        self.wrapped_adapter = wrapped_adapter
        self.show_reasoning = show_reasoning
        self.enable_few_shot = enable_few_shot
        self.name = f"{wrapped_adapter.name}_cot"

    def _build_few_shot_examples(self) -> list[dict[str, str]]:
        """构建少样本示例，帮助模型理解格式。"""
        return [
            {
                "role": "user",
                "content": "9.11和9.9哪个数字更大？",
            },
            {
                "role": "assistant",
                "content": """<思考>
1. 比较两个小数的大小，需要从整数部分开始比较
2. 9.11的整数部分是9，9.9的整数部分也是9，整数部分相同
3. 比较小数部分：0.11 vs 0.9
4. 0.11表示11/100 = 0.11
5. 0.9表示9/10 = 0.90 = 90/100
6. 90/100 > 11/100，所以0.9 > 0.11
7. 因此9.9 > 9.11
</思考>

<回答>
9.9 更大。9.9 = 9.90，而 9.11 = 9.11，所以 9.90 > 9.11。
</回答>""",
            },
            {
                "role": "user",
                "content": "如何提高Python代码的执行效率？",
            },
            {
                "role": "assistant",
                "content": """<思考>
1. Python执行效率问题通常涉及多个方面
2. 主要优化方向包括：算法优化、数据结构选择、并发处理、JIT编译等
3. 需要根据具体场景选择合适的优化策略
4. 应该先分析瓶颈，再针对性优化
5. 常用工具包括cProfile、line_profiler等
</思考>

<回答>
提高Python代码效率的主要方法：
1. 使用合适的数据结构（如集合代替列表进行查找）
2. 利用NumPy等优化库处理数值计算
3. 使用列表推导式代替循环
4. 启用多进程/异步处理并发任务
5. 使用PyPy或Cython加速关键代码
6. 先用profiler找到瓶颈再优化
</回答>""",
            },
        ]

    def _inject_cot_prompt(self, prompt: str, messages: list[dict[str, str]] | None) -> list[dict[str, str]]:
        """将 CoT 提示注入到消息列表中。"""
        if messages:
            # 如果已有消息列表，在开头添加系统提示，在最后的用户消息中包装CoT模板
            result_messages = []

            # 添加 CoT 系统提示
            result_messages.append({"role": "system", "content": self.COT_SYSTEM_PROMPT})

            # 添加少样本示例
            if self.enable_few_shot:
                result_messages.extend(self._build_few_shot_examples())

            # 处理原有消息
            for i, msg in enumerate(messages):
                if i == len(messages) - 1 and msg["role"] == "user":
                    # 最后一条用户消息用CoT模板包装
                    content = msg["content"]
                    if isinstance(content, str):
                        result_messages.append({"role": "user", "content": self.COT_USER_TEMPLATE.format(original_prompt=content)})
                    else:
                        result_messages.append(msg)
                elif msg["role"] == "system":
                    # 跳过原有的系统提示（已经添加了CoT系统提示）
                    continue
                else:
                    result_messages.append(msg)

            return result_messages
        else:
            # 简单提示，构建新消息列表
            result_messages = [{"role": "system", "content": self.COT_SYSTEM_PROMPT}]

            if self.enable_few_shot:
                result_messages.extend(self._build_few_shot_examples())

            result_messages.append({"role": "user", "content": self.COT_USER_TEMPLATE.format(original_prompt=prompt)})
            return result_messages

    def _extract_answer(self, text: str) -> tuple[str, str]:
        """从模型输出中提取思考过程和最终答案。

        Returns:
            (reasoning, answer) 元组
        """
        # 尝试提取 <思考> 和 <回答> 标签内容
        reasoning_match = re.search(r"<思考>(.*?)</思考>", text, re.DOTALL)
        answer_match = re.search(r"<回答>(.*?)</回答>", text, re.DOTALL)

        reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
        answer = answer_match.group(1).strip() if answer_match else text

        # 如果没有找到标签，尝试其他分隔方式
        if not reasoning and not answer_match:
            # 尝试通过关键词分割
            if "思考：" in text or "推理：" in text or "分析：" in text:
                parts = re.split(r"(?:回答|答案|结论)[：:]", text)
                if len(parts) >= 2:
                    reasoning = parts[0].strip()
                    answer = parts[1].strip()
                else:
                    answer = text
            else:
                # 没有明确的思考标记，直接返回全文作为答案
                answer = text

        return reasoning, answer

    async def generate(self, prompt: str, **kwargs: Any) -> SimpleCompletionResult:
        """生成带有思维链的响应。"""
        # 注入 CoT 提示
        messages = kwargs.get("messages")
        cot_messages = self._inject_cot_prompt(prompt, messages)

        # 更新 kwargs，使用注入了 CoT 的消息列表
        cot_kwargs = kwargs.copy()
        cot_kwargs["messages"] = cot_messages

        # 可能需要更多的 max_tokens 来容纳思考过程
        if "max_tokens" in cot_kwargs:
            cot_kwargs["max_tokens"] = int(cot_kwargs["max_tokens"] * 1.5)

        # 调用底层适配器
        result = await self.wrapped_adapter.generate(prompt, **cot_kwargs)

        # 提取推理过程和答案
        reasoning, answer = self._extract_answer(result.text)

        # 根据配置决定是否在最终结果中显示推理过程
        if self.show_reasoning and reasoning:
            final_text = f"【思考过程】\n{reasoning}\n\n【最终答案】\n{answer}"
        else:
            final_text = answer

        return SimpleCompletionResult(text=final_text, usage=result.usage)

    async def count_tokens(self, text: str) -> int:
        """委托给底层适配器计算 token。"""
        return await self.wrapped_adapter.count_tokens(text)


def wrap_adapter_with_cot(
    adapter: ModelAdapter,
    show_reasoning: bool = False,
    enable_few_shot: bool = True,
) -> CoTWrapper:
    """便捷函数：将任何适配器包装为支持 CoT 的版本。

    Args:
        adapter: 要包装的适配器
        show_reasoning: 是否显示推理过程
        enable_few_shot: 是否启用少样本示例

    Returns:
        包装后的 CoTWrapper 实例
    """
    return CoTWrapper(adapter, show_reasoning=show_reasoning, enable_few_shot=enable_few_shot)

