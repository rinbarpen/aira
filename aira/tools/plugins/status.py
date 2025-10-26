from __future__ import annotations

from typing import Any

from aira.memory.service import MemoryService
from aira.models import build_gateway


def summarize_state(session_id: str, limit: int = 20, model: str = "gemini:gemini-1.5-flash") -> dict[str, Any]:
    memory_service = MemoryService()
    conversations = await memory_service.fetch_recent(session_id, limit)  # type: ignore
    context = "\n".join(record.content for record in conversations)
    prompt = (
        "请根据以下对话内容，总结当前会话状态，分为以下板块：\n"
        "- 总结\n"
        "- 用户需求\n"
        "- 下一步建议\n"
        "- 注意事项\n\n"
        f"对话内容：\n{context}"
    )
    gateway = build_gateway()
    result = gateway.get(model).generate(prompt)
    return {"summary": result.text.strip()}
