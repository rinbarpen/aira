"""对话编排器占位实现。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aira.core.config import get_app_config, get_persona_config, get_mcp_config
from aira.memory.service import MemoryRecord, MemoryService
from aira.models import build_gateway, get_planner_model
from aira.stats.tracker import StatRecord, StatsTracker
from aira.monitor import Monitor, Pricing
from aira.memory.repository import SqliteRepository
from aira.tools.registry import ToolRegistry
from aira.tools.runner import ToolExecutionError, ToolRunner


@dataclass
class DialogueContext:
    session_id: str
    persona_id: str
    history: list[dict[str, Any]]
    metadata: dict[str, Any]


class DialogueOrchestrator:
    """负责协调记忆检索、模型调用、工具调用的主控制器。"""

    def __init__(self) -> None:
        self._memory = MemoryService()
        self._gateway = build_gateway()
        self._tool_registry = ToolRegistry()
        self._tool_runner = ToolRunner(self._tool_registry)
        self._stats = StatsTracker()
        self._app_config = get_app_config()
        storage = self._app_config.get("storage", {})
        pricing_cfg = self._app_config.get("pricing", {})
        pricing_table = {k: Pricing(**v) for k, v in pricing_cfg.items()}
        self._repo = SqliteRepository(Path(storage.get("sqlite_path", "data/aira.db")))
        self._monitor = Monitor(self._repo, pricing_table)
        self._planner_model = get_planner_model()
        self._load_tools()

    async def handle_turn(self, context: DialogueContext, user_input: str) -> dict[str, Any]:
        """处理单轮对话请求。"""

        persona_config = get_persona_config(context.persona_id)
        emoji_enabled = persona_config.get("persona", {}).get("behavior", {}).get("emoji", False)
        memories = await self._memory.fetch_recent(context.session_id)
        plan = await self._plan_reply(context, persona_config, memories, user_input)
        prompt = self._compose_prompt(context, persona_config, memories, user_input, emoji_enabled, plan)
        model_name = self._app_config["app"].get("default_model")
        async with self._stats.timer() as timer:
            completion = await self._gateway.generate(model_name, prompt)
        stat = StatRecord(
            request_id=context.metadata.get("request_id", context.session_id),
            model=model_name,
            tokens_in=completion.usage.get("input_tokens", 0),
            tokens_out=completion.usage.get("output_tokens", 0),
            extra={"duration": getattr(timer, "duration", 0.0)},
        )
        self._stats.record(stat)
        await self._monitor.record(
            request_id=stat.request_id,
            session_id=context.session_id,
            model=model_name,
            tokens_in=stat.tokens_in,
            tokens_out=stat.tokens_out,
            duration_ms=float(stat.extra.get("duration", 0.0)) * 1000.0,
        )

        reply = completion.text

        tool_calls = completion.usage.get("tool_calls", []) if isinstance(completion.usage, dict) else []
        tool_results: list[dict[str, Any]] = []
        live2d_intent = context.metadata.get("live2d_action")
        if live2d_intent:
            try:
                result = await self._tool_runner.invoke("live2d_action", live2d_intent)
                tool_results.append({"tool": "live2d_action", "result": result})
            except ToolExecutionError as exc:
                tool_results.append({"tool": "live2d_action", "error": str(exc)})
        if context.metadata.get("suggest_replies"):
            try:
                result = await self._tool_runner.invoke("suggest_replies", {"prompt": reply})
                tool_results.append({"tool": "suggest_replies", "result": result["result"]})
            except ToolExecutionError as exc:
                tool_results.append({"tool": "suggest_replies", "error": str(exc)})
        if context.metadata.get("summarize_state"):
            try:
                result = await self._tool_runner.invoke("summarize_state", {"session_id": context.session_id})
                tool_results.append({"tool": "summarize_state", "result": result["result"]})
            except ToolExecutionError as exc:
                tool_results.append({"tool": "summarize_state", "error": str(exc)})

        if emoji_enabled and not any(call.get("id") == "sticker_picker" for call in tool_calls):
            sentiment = context.metadata.get("sentiment") or "happy"
            try:
                result = await self._tool_runner.invoke("sticker_picker", {"mood": sentiment})
                tool_results.append({"tool": "sticker_picker", "result": result})
                # 处理嵌套的结果结构
                sticker_data = result.get("result", result)
                if "url" in sticker_data:
                    reply = f"{reply}\n[贴纸] {sticker_data['url']}"
            except ToolExecutionError as exc:
                tool_results.append({"tool": "sticker_picker", "error": str(exc)})

        for call in tool_calls:
            try:
                result = await self._tool_runner.invoke(call["id"], call.get("input", {}))
                tool_results.append({"tool": call["id"], "result": result})
            except ToolExecutionError as exc:
                tool_results.append({"tool": call["id"], "error": str(exc)})

        if not context.metadata.get("memory_barrier"):
            await self._memory.store(
                context.session_id,
                MemoryRecord(content=user_input, category="interaction", score=1.0, metadata={}),
            )
            await self._memory.add_conversation(
                context.session_id,
                role="user",
                content=user_input,
            )
            await self._memory.add_conversation(
                context.session_id,
                role="assistant",
                content=reply,
                model=model_name,
                provider=model_name.split(":", 1)[0] if ":" in model_name else model_name,
                thought=plan,
            )

        return {
            "reply": reply,
            "session_id": context.session_id,
            "persona_id": context.persona_id,
            "memories": [record.content for record in memories],
            "plan": plan,
            "tools": tool_results,
            "stats": stat,
        }

    async def _plan_reply(
        self,
        context: DialogueContext,
        persona_config: dict[str, Any],
        memories: list[MemoryRecord],
        user_input: str,
    ) -> str:
        if not self._planner_model:
            return ""
        planning_prompt = (
            "你是对话规划器，请根据以下上下文推导回复思路，输出思考步骤列表。\n"
            f"记忆：{'; '.join(m.content for m in memories)}\n"
            f"历史：{'; '.join(item.get('content', '') for item in context.history)}\n"
            f"用户输入：{user_input}\n"
            "请输出计划，例如：\n1. ...\n2. ..."
        )
        result = await self._gateway.generate(self._planner_model, planning_prompt)
        return result.text.strip()

    def _compose_prompt(
        self,
        context: DialogueContext,
        persona_config: dict[str, Any],
        memories: list[MemoryRecord],
        user_input: str,
        emoji_enabled: bool = False,
        plan: str = "",
    ) -> str:
        persona_prompt = persona_config.get("persona", {}).get("prompts", {}).get("system", "")
        if emoji_enabled:
            persona_prompt += "\n你可以在表达情感时使用 emoji，并在合适的时候附带贴纸链接。"
        if plan:
            persona_prompt += f"\n以下是你的思考步骤，请遵循：\n{plan}\n"
        memory_section = "\n".join(record.content for record in memories)
        history_section = "\n".join(item.get("content", "") for item in context.history)
        return (
            f"{persona_prompt}\n\n"
            f"[Memory]\n{memory_section}\n\n"
            f"[History]\n{history_section}\n\n"
            f"[User]\n{user_input}"
        )

    def _load_tools(self) -> None:
        tools_config = self._app_config.get("tools", {})
        mcp_config = get_mcp_config()
        self._tool_registry.register_from_config(tools_config.get("plugins", []), mcp_config=mcp_config)

