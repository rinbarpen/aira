"""外部 Chain-of-Thought 嵌入包装器。

该包装器使用一个辅助模型生成思维链内容，再将思维链注入到
目标模型的提示中，帮助目标模型在回答时参考详细推理。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from aira.models.gateway import ModelAdapter, SimpleCompletionResult


@dataclass(slots=True)
class CoTGeneratorOptions:
    model: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None


class CoTEmbeddingWrapper(ModelAdapter):
    """将外部模型生成的思维链嵌入到目标模型提示的包装器。"""

    DEFAULT_COT_PROMPT = (
        "你是一名能够生成链式思维 (CoT) 的推理助手。请只输出清晰、逐步的推理步"
        "骤，不要给出最终答案。确保推理覆盖问题的关键点，并使用有序列表。\n\n"
        "用户问题：{original_prompt}\n\n"
        "推理步骤："
    )

    DEFAULT_SYSTEM_PROMPT = (
        "以下内容来自辅助模型生成的推理链，请在回答用户问题时充分参考，但不要"
        "泄露其来源。你需要基于该推理链得出自己的最终答案。\n\n"
        "[外部推理链]\n{reasoning}\n"
    )

    def __init__(
        self,
        wrapped_adapter: ModelAdapter,
        generator_adapter: ModelAdapter,
        *,
        generator_options: CoTGeneratorOptions | None = None,
        cot_prompt_template: str | None = None,
        system_prompt_template: str | None = None,
        show_reasoning: bool = False,
    ) -> None:
        self.wrapped_adapter = wrapped_adapter
        self.generator_adapter = generator_adapter
        self.generator_options = generator_options or CoTGeneratorOptions()
        self.cot_prompt_template = cot_prompt_template or self.DEFAULT_COT_PROMPT
        self.system_prompt_template = system_prompt_template or self.DEFAULT_SYSTEM_PROMPT
        self.show_reasoning = show_reasoning
        self.name = wrapped_adapter.name

    async def generate(self, prompt: str, **kwargs: Any) -> SimpleCompletionResult:
        original_messages = kwargs.get("messages")
        base_prompt = self._extract_user_prompt(prompt, original_messages)

        cot_prompt = self.cot_prompt_template.format(original_prompt=base_prompt)
        cot_kwargs = self._build_generator_kwargs()
        cot_result = await self.generator_adapter.generate(cot_prompt, **cot_kwargs)
        reasoning = cot_result.text.strip()

        final_messages = self._inject_reasoning(original_messages, prompt, reasoning)
        final_kwargs = kwargs.copy()
        final_kwargs["messages"] = final_messages

        result = await self.wrapped_adapter.generate(prompt, **final_kwargs)

        merged_usage: Dict[str, Any] = dict(result.usage or {})
        generator_usage = cot_result.usage or {}
        if generator_usage:
            merged_usage.setdefault("cot_usage", {})
            merged_usage["cot_usage"].update(
                {
                    "input_tokens": generator_usage.get("input_tokens", 0),
                    "output_tokens": generator_usage.get("output_tokens", 0),
                }
            )

        final_text = result.text
        if self.show_reasoning and reasoning:
            final_text = f"【外部思维链】\n{reasoning}\n\n【模型回答】\n{final_text}".strip()

        return SimpleCompletionResult(text=final_text, usage=merged_usage)

    async def count_tokens(self, text: str) -> int:
        return await self.wrapped_adapter.count_tokens(text)

    def _build_generator_kwargs(self) -> Dict[str, Any]:
        options = self.generator_options
        kwargs: Dict[str, Any] = {}
        if options.model:
            kwargs["model"] = options.model
        if options.max_tokens is not None:
            kwargs["max_tokens"] = options.max_tokens
        if options.temperature is not None:
            kwargs["temperature"] = options.temperature
        return kwargs

    def _inject_reasoning(
        self,
        messages: Optional[List[dict[str, Any]]],
        prompt: str,
        reasoning: str,
    ) -> List[dict[str, Any]]:
        reasoning_message = {
            "role": "system",
            "content": self.system_prompt_template.format(reasoning=reasoning or "(无可用推理链)"),
        }

        if not messages:
            return [reasoning_message, {"role": "user", "content": prompt}]

        final_messages: List[dict[str, Any]] = [reasoning_message]
        final_messages.extend(messages)
        return final_messages

    @staticmethod
    def _extract_user_prompt(prompt: str, messages: Optional[Iterable[dict[str, Any]]]) -> str:
        if not messages:
            return prompt

        sequence: List[dict[str, Any]]
        if isinstance(messages, list):
            sequence = messages
        else:
            sequence = list(messages)

        for message in reversed(sequence):
            if message.get("role") == "user":
                content = message.get("content", "")
                if isinstance(content, str) and content.strip():
                    return content
        return prompt


