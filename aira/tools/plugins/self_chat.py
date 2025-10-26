from __future__ import annotations

import re
from typing import Any, Dict, List

from aira.core.config import get_app_config
from aira.models import build_gateway, get_planner_model


async def self_chat(
    goal: str,
    *,
    max_turns: int = 6,
    model: str | None = None,
    planner_model: str | None = None,
    temperature: float = 0.7,
) -> dict[str, Any]:
    """让 Aira 自行与 LLM 对话以逐步求解问题."""

    config = get_app_config()
    default_model = model or config["app"].get("default_model")
    planner = planner_model or get_planner_model()
    gateway = build_gateway()

    system_prompt = (
        "你正在为用户目标进行自我对话，请遵循以下格式：\n"
        "- 每轮给出条理清晰的思考，使用 `THOUGHT:` 前缀。\n"
        "- 如需尝试方案，可给出 `ACTION:` 描述。\n"
        "- 当确定最终答案时，以 `FINAL:` 前缀输出结论与建议。\n"
        "目标：" + goal
    )

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
    ]
    transcript: List[dict[str, str]] = []
    final_answer: str | None = None

    for _ in range(max_turns):
        response = await gateway.generate(
            default_model,
            goal,
            messages=messages,
            temperature=temperature,
            max_tokens=800,
        )
        text = response.text.strip()
        transcript.append({"assistant": text})
        messages.append({"role": "assistant", "content": text})

        match = re.search(r"FINAL:(.*)", text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            final_answer = match.group(1).strip()
            break
        messages.append({"role": "user", "content": "请继续。"})

    if not final_answer and transcript:
        final_answer = transcript[-1]["assistant"]

    plan_summary = ""
    if planner:
        planner_prompt = (
            "请总结以下自对话的关键步骤，输出要点列表。\n" + "\n".join(item["assistant"] for item in transcript)
        )
        planner_response = await gateway.generate(
            planner,
            planner_prompt,
            temperature=0.3,
            max_tokens=400,
        )
        plan_summary = planner_response.text.strip()

    return {
        "goal": goal,
        "transcript": transcript,
        "final_answer": final_answer or "",
        "summary": plan_summary,
        "model": default_model,
    }
