"""对话编排器占位实现。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

from aira.core.config import get_app_config, get_persona_config, get_mcp_config
from aira.memory.service import MemoryRecord, MemoryService
from aira.models import build_gateway, get_planner_model
from aira.stats.tracker import StatRecord, StatsTracker
from aira.monitor import Monitor, Pricing
from aira.memory.repository import SqliteRepository
from aira.tools.registry import ToolRegistry
from aira.tools.runner import ToolExecutionError, ToolRunner

# 高级功能模块（可选依赖）
try:
    from aira.persona import PersonaEvolutionTracker
except ImportError:
    PersonaEvolutionTracker = None  # type: ignore

try:
    from aira.vision import VisionCognitionSystem
except ImportError:
    VisionCognitionSystem = None  # type: ignore

try:
    from aira.avatar import AvatarManager
except ImportError:
    AvatarManager = None  # type: ignore


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
        
        # 高级功能组件
        self._persona_trackers: dict[str, PersonaEvolutionTracker] = {}
        self._vision_system: VisionCognitionSystem | None = None
        self._avatar_manager: AvatarManager | None = None
        
        # 根据配置初始化高级功能
        self._init_advanced_features()
        
        self._load_tools()

    async def handle_turn(self, context: DialogueContext, user_input: str) -> dict[str, Any]:
        """处理单轮对话请求。"""

        persona_config = get_persona_config(context.persona_id)
        emoji_enabled = persona_config.get("persona", {}).get("behavior", {}).get("emoji", False)
        
        # 获取人格进化追踪器
        persona_tracker = self._get_persona_tracker(context.persona_id)
        
        # 捕获用户视觉状态（如果启用）
        user_state = None
        if self._vision_system:
            user_state = self._vision_system.capture_user_state()
            if user_state and user_state.face_detected:
                # 将用户状态添加到上下文
                context.metadata["user_emotion"] = user_state.emotion.value
                context.metadata["user_posture"] = user_state.posture.value
                context.metadata["user_engagement"] = user_state.engagement_level
                context.metadata["user_fatigue"] = user_state.fatigue_level
        
        memories = await self._memory.fetch_recent(context.session_id)
        plan = await self._plan_reply(context, persona_config, memories, user_input)
        
        # 生成prompt，包含人格进化提示
        prompt = self._compose_prompt(context, persona_config, memories, user_input, emoji_enabled, plan)
        
        # 如果有人格追踪器，添加人格特征提示
        if persona_tracker:
            personality_prompt = persona_tracker.get_personality_prompt()
            if personality_prompt:
                prompt = f"{prompt}\n\n{personality_prompt}"
        
        # 如果有用户状态，添加到prompt
        if user_state and user_state.face_detected:
            state_desc = self._vision_system.get_state_description(user_state)
            prompt = f"{prompt}\n\n【用户状态】{state_desc}\n请根据用户的当前状态调整你的回复。"
        
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
        
        # 驱动Avatar表达（如果启用）
        if self._avatar_manager and user_state:
            try:
                await self._avatar_manager.react_to_user_state(
                    user_emotion=user_state.emotion.value,
                    user_posture=user_state.posture.value,
                    engagement_level=user_state.engagement_level,
                )
            except Exception:
                pass  # 静默失败，不影响主流程

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
        
        # 记录到人格进化系统
        if persona_tracker:
            # 计算情感得分
            sentiment = 0.0
            if user_state:
                emotion_sentiment_map = {
                    "happy": 0.8,
                    "sad": -0.6,
                    "angry": -0.8,
                    "surprised": 0.3,
                    "neutral": 0.0,
                    "tired": -0.4,
                    "focused": 0.5,
                }
                sentiment = emotion_sentiment_map.get(user_state.emotion.value, 0.0)
            
            # 获取反馈（如果有）
            feedback = context.metadata.get("feedback")
            
            persona_tracker.record_interaction(
                user_input=user_input,
                assistant_response=reply,
                feedback=feedback,
                sentiment=sentiment,
                metadata=context.metadata,
            )

        return {
            "reply": reply,
            "session_id": context.session_id,
            "persona_id": context.persona_id,
            "memories": [record.content for record in memories],
            "plan": plan,
            "tools": tool_results,
            "stats": stat,
            "user_state": {
                "emotion": user_state.emotion.value if user_state else None,
                "posture": user_state.posture.value if user_state else None,
                "engagement": user_state.engagement_level if user_state else None,
            } if user_state else None,
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
        
        # 添加说话风格设置
        speaking_style = persona_config.get("persona", {}).get("speaking_style", {})
        if speaking_style.get("use_inner_voice", False):
            style_desc = speaking_style.get("description", "")
            persona_prompt += f"\n\n【说话风格】\n{style_desc}"
        
        if emoji_enabled:
            persona_prompt += "\n你可以在表达情感时使用 emoji，并在合适的时候附带贴纸链接。"
        
        # 处理角色扮演模式
        role_play = context.metadata.get("role_play")
        if role_play:
            persona_prompt += f"\n\n【角色扮演模式】\n你现在要扮演：{role_play}\n请完全进入这个角色，用该角色的方式说话和思考。"
        
        if plan:
            persona_prompt += f"\n\n【思考步骤】\n{plan}"
        
        memory_section = "\n".join(record.content for record in memories)
        history_section = "\n".join(item.get("content", "") for item in context.history)
        return (
            f"{persona_prompt}\n\n"
            f"[Memory]\n{memory_section}\n\n"
            f"[History]\n{history_section}\n\n"
            f"[User]\n{user_input}"
        )

    async def handle_turn_stream(
        self, 
        context: DialogueContext, 
        user_input: str
    ) -> AsyncIterator[dict[str, Any]]:
        """处理单轮对话请求（流式版本）。
        
        Yields:
            包含文本块或元数据的字典
        """
        persona_config = get_persona_config(context.persona_id)
        emoji_enabled = persona_config.get("persona", {}).get("behavior", {}).get("emoji", False)
        memories = await self._memory.fetch_recent(context.session_id)
        plan = await self._plan_reply(context, persona_config, memories, user_input)
        prompt = self._compose_prompt(context, persona_config, memories, user_input, emoji_enabled, plan)
        model_name = self._app_config["app"].get("default_model")
        
        # 获取完整响应（这里简化处理，实际应该用模型的流式接口）
        async with self._stats.timer() as timer:
            completion = await self._gateway.generate(model_name, prompt)
        
        reply = completion.text
        
        # 模拟流式输出：逐字符或逐词输出
        import asyncio
        words = []
        current_word = ""
        
        for char in reply:
            current_word += char
            if char in (' ', '\n', '。', '！', '？', '，', '、', ',', '.', '!', '?'):
                if current_word.strip():
                    words.append(current_word)
                    yield {"type": "chunk", "content": current_word}
                    await asyncio.sleep(0.01)  # 短暂延迟模拟流式
                    current_word = ""
        
        if current_word:
            words.append(current_word)
            yield {"type": "chunk", "content": current_word}
        
        # 处理统计和记忆存储
        stat = StatRecord(
            request_id=context.metadata.get("request_id", context.session_id),
            model=model_name,
            tokens_in=completion.usage.get("input_tokens", 0),
            tokens_out=completion.usage.get("output_tokens", 0),
            extra={"duration": getattr(timer, "duration", 0.0)},
        )
        self._stats.record(stat)
        
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
        
        # 发送完成信号
        yield {
            "type": "done",
            "session_id": context.session_id,
            "persona_id": context.persona_id,
            "stats": {
                "tokens_in": stat.tokens_in,
                "tokens_out": stat.tokens_out,
                "duration": stat.extra.get("duration", 0.0),
            }
        }

    def _init_advanced_features(self) -> None:
        """初始化高级功能组件。"""
        import logging
        
        # 初始化视觉认知系统
        vision_config = self._app_config.get("vision", {})
        if vision_config.get("enabled", False):
            if VisionCognitionSystem is None:
                logging.warning("视觉认知系统依赖未安装，请运行: uv pip install -e '.[vision]'")
            else:
                try:
                    self._vision_system = VisionCognitionSystem(
                        camera_id=vision_config.get("camera_id", 0),
                        enable_emotion=vision_config.get("enable_emotion_detection", True),
                        enable_posture=vision_config.get("enable_posture_detection", True),
                    )
                    self._vision_system.start_capture()
                except Exception as e:
                    logging.warning(f"无法初始化视觉系统: {e}")
                    self._vision_system = None
        
        # 初始化Avatar管理器
        avatar_config = self._app_config.get("avatar", {})
        if avatar_config.get("enabled", False):
            if AvatarManager is None:
                logging.warning("Avatar控制系统依赖未安装，请运行: uv pip install -e '.[avatar]'")
            else:
                try:
                    self._avatar_manager = AvatarManager()
                    # 可以在这里注册默认控制器
                except Exception as e:
                    logging.warning(f"无法初始化Avatar管理器: {e}")
                    self._avatar_manager = None
    
    def _get_persona_tracker(self, persona_id: str) -> PersonaEvolutionTracker | None:
        """获取或创建人格进化追踪器。"""
        if PersonaEvolutionTracker is None:
            return None
        
        if persona_id not in self._persona_trackers:
            evolution_config = self._app_config.get("persona_evolution", {})
            if evolution_config.get("enabled", True):
                storage_dir = Path(evolution_config.get("storage_dir", "data/evolution"))
                self._persona_trackers[persona_id] = PersonaEvolutionTracker(
                    persona_id=persona_id,
                    storage_dir=storage_dir,
                )
        return self._persona_trackers.get(persona_id)
    
    def _load_tools(self) -> None:
        tools_config = self._app_config.get("tools", {})
        mcp_config = get_mcp_config()
        self._tool_registry.register_from_config(tools_config.get("plugins", []), mcp_config=mcp_config)

