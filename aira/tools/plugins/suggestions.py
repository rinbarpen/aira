from __future__ import annotations

from typing import Any, Sequence

from aira.models import build_gateway


STYLE_PRESETS = {
    "default": "保持友好和自然",
    "formal": "使用正式、礼貌的措辞回复",
    "casual": "语气轻松，像朋友一样交流",
    "concise": "尽量简洁扼要",
    "empathetic": "多给安慰和共情",
    "humorous": "加入轻松幽默的表达",
}


def suggest_replies(
    prompt: str,
    *,
    count: int = 3,
    model: str = "gemini:gemini-1.5-flash",
    style: str = "default",
    candidates: Sequence[str] | None = None,
) -> dict[str, Any]:
    gateway = build_gateway()
    system_prompt = (
        "你是对话建议助手，根据以下要求生成备选回复。"
        "请使用项目符号列出，避免重复用户原话。"
    )
    style_hint = STYLE_PRESETS.get(style, style)
    suggestions: list[str] = []
    target_models = list(candidates) if candidates else [model]

    for idx in range(count):
        target_model = target_models[min(idx, len(target_models) - 1)]
        response = gateway.get(target_model).generate(
            prompt,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"请给出备选回复 #{idx + 1}，遵循风格：{style_hint}。"
                        f"\n上下文：{prompt}"
                    ),
                },
            ],
        )
        suggestions.append(response.text.strip())

    return {"suggestions": suggestions, "style": style, "models": target_models}
