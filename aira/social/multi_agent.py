"""多Agent社交系统 - 支持多个人格代理之间的对话和社交互动。"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator

from aira.dialogue.orchestrator import DialogueContext, DialogueOrchestrator
from aira.core.config import get_persona_config


logger = logging.getLogger(__name__)


class InteractionType(str, Enum):
    """交互类型。"""
    
    DIALOGUE = "dialogue"  # 对话
    DEBATE = "debate"  # 辩论
    COLLABORATION = "collaboration"  # 协作
    CASUAL_CHAT = "casual_chat"  # 闲聊
    TEACHING = "teaching"  # 教学
    ROLEPLAY = "roleplay"  # 角色扮演


class AgentRole(str, Enum):
    """Agent角色类型。"""
    
    LEADER = "leader"  # 主导者
    PARTICIPANT = "participant"  # 参与者
    OBSERVER = "observer"  # 观察者
    MODERATOR = "moderator"  # 主持人


@dataclass
class AgentProfile:
    """Agent档案。"""
    
    agent_id: str
    persona_id: str
    display_name: str
    role: AgentRole
    personality_traits: dict[str, float]
    relationship_map: dict[str, float] = field(default_factory=dict)  # 与其他agent的关系
    conversation_count: int = 0


@dataclass
class SocialMessage:
    """社交消息。"""
    
    message_id: str
    from_agent: str
    to_agent: str | None  # None表示群发
    content: str
    interaction_type: InteractionType
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    references: list[str] = field(default_factory=list)  # 引用的消息ID


@dataclass
class SocialScene:
    """社交场景定义。"""
    
    scene_id: str
    name: str
    description: str
    interaction_type: InteractionType
    participants: list[str]  # agent_id列表
    topic: str | None = None
    objectives: list[str] = field(default_factory=list)
    max_turns: int = 20
    current_turn: int = 0
    created_at: datetime = field(default_factory=datetime.now)


class MultiAgentOrchestrator:
    """多Agent编排器 - 管理多个AI代理之间的交互。"""
    
    def __init__(self):
        self.agents: dict[str, AgentProfile] = {}
        self.orchestrators: dict[str, DialogueOrchestrator] = {}
        self.active_scenes: dict[str, SocialScene] = {}
        self.message_history: dict[str, list[SocialMessage]] = {}
    
    def register_agent(
        self,
        persona_id: str,
        display_name: str | None = None,
        role: AgentRole = AgentRole.PARTICIPANT,
    ) -> str:
        """注册一个Agent。"""
        agent_id = f"agent_{persona_id}_{uuid.uuid4().hex[:8]}"
        
        # 获取persona配置
        persona_config = get_persona_config(persona_id)
        
        # 提取性格特征（如果有）
        personality_traits = {}
        if "persona" in persona_config:
            style = persona_config["persona"].get("style", {})
            personality_traits = {
                "formality": 0.7 if style.get("formality") == "formal" else 0.3,
                "warmth": 0.8 if style.get("tone") == "warm" else 0.5,
                "emoji_usage": 1.0 if style.get("emoji", False) else 0.0,
            }
        
        profile = AgentProfile(
            agent_id=agent_id,
            persona_id=persona_id,
            display_name=display_name or persona_config.get("display_name", persona_id),
            role=role,
            personality_traits=personality_traits,
        )
        
        self.agents[agent_id] = profile
        
        # 为每个agent创建独立的orchestrator
        self.orchestrators[agent_id] = DialogueOrchestrator()
        
        logger.info(f"注册Agent: {agent_id} ({display_name})")
        return agent_id
    
    def create_scene(
        self,
        name: str,
        description: str,
        interaction_type: InteractionType,
        participants: list[str],
        topic: str | None = None,
        max_turns: int = 20,
    ) -> str:
        """创建一个社交场景。"""
        scene_id = f"scene_{uuid.uuid4().hex[:8]}"
        
        scene = SocialScene(
            scene_id=scene_id,
            name=name,
            description=description,
            interaction_type=interaction_type,
            participants=participants,
            topic=topic,
            max_turns=max_turns,
        )
        
        self.active_scenes[scene_id] = scene
        self.message_history[scene_id] = []
        
        logger.info(f"创建场景: {scene_id} - {name}")
        return scene_id
    
    async def send_message(
        self,
        scene_id: str,
        from_agent: str,
        content: str,
        to_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SocialMessage:
        """在场景中发送消息。"""
        if scene_id not in self.active_scenes:
            raise ValueError(f"场景不存在: {scene_id}")
        
        scene = self.active_scenes[scene_id]
        
        message = SocialMessage(
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            interaction_type=scene.interaction_type,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        
        self.message_history[scene_id].append(message)
        
        # 更新关系
        if from_agent in self.agents:
            self.agents[from_agent].conversation_count += 1
        
        return message
    
    async def run_scene(self, scene_id: str) -> AsyncIterator[dict[str, Any]]:
        """运行一个社交场景（生成器模式）。"""
        if scene_id not in self.active_scenes:
            raise ValueError(f"场景不存在: {scene_id}")
        
        scene = self.active_scenes[scene_id]
        
        # 生成场景开场白
        yield {
            "type": "scene_start",
            "scene_id": scene_id,
            "scene_name": scene.name,
            "participants": [
                {
                    "agent_id": pid,
                    "name": self.agents[pid].display_name,
                }
                for pid in scene.participants
                if pid in self.agents
            ],
        }
        
        # 轮流对话
        current_speaker_idx = 0
        previous_content = scene.topic or "开始对话"
        
        while scene.current_turn < scene.max_turns:
            # 确定当前说话者
            current_speaker = scene.participants[current_speaker_idx % len(scene.participants)]
            
            if current_speaker not in self.agents:
                logger.warning(f"Agent不存在: {current_speaker}")
                break
            
            # 生成对话
            response = await self._generate_agent_response(
                scene_id=scene_id,
                agent_id=current_speaker,
                context_messages=self.message_history[scene_id][-5:],
                previous_content=previous_content,
            )
            
            # 发送消息
            message = await self.send_message(
                scene_id=scene_id,
                from_agent=current_speaker,
                content=response,
            )
            
            # 输出消息
            yield {
                "type": "message",
                "agent_id": current_speaker,
                "agent_name": self.agents[current_speaker].display_name,
                "content": response,
                "turn": scene.current_turn,
            }
            
            previous_content = response
            scene.current_turn += 1
            current_speaker_idx += 1
            
            # 短暂延迟，模拟思考时间
            await asyncio.sleep(0.5)
        
        # 场景结束
        yield {
            "type": "scene_end",
            "scene_id": scene_id,
            "total_turns": scene.current_turn,
            "summary": await self._summarize_scene(scene_id),
        }
    
    async def _generate_agent_response(
        self,
        scene_id: str,
        agent_id: str,
        context_messages: list[SocialMessage],
        previous_content: str,
    ) -> str:
        """生成Agent的回复。"""
        if agent_id not in self.orchestrators:
            return "..."
        
        orchestrator = self.orchestrators[agent_id]
        agent = self.agents[agent_id]
        scene = self.active_scenes[scene_id]
        
        # 构建对话历史
        history = [
            {
                "role": "assistant" if msg.from_agent == agent_id else "user",
                "content": f"{self.agents[msg.from_agent].display_name}: {msg.content}",
            }
            for msg in context_messages
        ]
        
        # 构建上下文
        context = DialogueContext(
            session_id=scene_id,
            persona_id=agent.persona_id,
            history=history,
            metadata={
                "scene_type": scene.interaction_type.value,
                "role": agent.role.value,
                "other_participants": [
                    self.agents[pid].display_name
                    for pid in scene.participants
                    if pid != agent_id and pid in self.agents
                ],
            },
        )
        
        # 构建输入提示
        input_prompt = self._build_scene_prompt(scene, agent, previous_content)
        
        # 生成回复
        result = await orchestrator.handle_turn(context, input_prompt)
        
        return result["reply"]
    
    def _build_scene_prompt(
        self,
        scene: SocialScene,
        agent: AgentProfile,
        previous_content: str,
    ) -> str:
        """构建场景特定的提示。"""
        base = f"当前场景：{scene.name}\n{scene.description}\n"
        
        if scene.topic:
            base += f"话题：{scene.topic}\n"
        
        # 根据交互类型调整提示
        if scene.interaction_type == InteractionType.DEBATE:
            base += f"\n这是一场辩论。你的角色是{agent.role.value}。请针对以下观点发表你的看法：\n{previous_content}"
        elif scene.interaction_type == InteractionType.COLLABORATION:
            base += f"\n这是协作讨论。请基于以下内容继续推进讨论：\n{previous_content}"
        elif scene.interaction_type == InteractionType.TEACHING:
            if agent.role == AgentRole.LEADER:
                base += f"\n你是教师。请教授或解释以下内容：\n{previous_content}"
            else:
                base += f"\n你是学生。请提问或回应：\n{previous_content}"
        elif scene.interaction_type == InteractionType.CASUAL_CHAT:
            base += f"\n轻松闲聊。回应以下内容：\n{previous_content}"
        else:
            base += f"\n{previous_content}"
        
        return base
    
    async def _summarize_scene(self, scene_id: str) -> str:
        """总结场景内容。"""
        if scene_id not in self.message_history:
            return "无内容"
        
        messages = self.message_history[scene_id]
        
        if not messages:
            return "场景中没有发生对话"
        
        # 简单总结
        agent_names = set(
            self.agents[msg.from_agent].display_name
            for msg in messages
            if msg.from_agent in self.agents
        )
        
        return (
            f"参与者：{', '.join(agent_names)}；"
            f"共{len(messages)}条消息；"
            f"主要讨论了{self.active_scenes[scene_id].topic or '多个话题'}。"
        )
    
    def get_agent_relationship(self, agent_id1: str, agent_id2: str) -> float:
        """获取两个Agent之间的关系值（-1.0到1.0）。"""
        if agent_id1 not in self.agents:
            return 0.0
        
        return self.agents[agent_id1].relationship_map.get(agent_id2, 0.0)
    
    def update_agent_relationship(
        self,
        agent_id1: str,
        agent_id2: str,
        delta: float,
    ) -> None:
        """更新Agent之间的关系。"""
        if agent_id1 in self.agents:
            current = self.agents[agent_id1].relationship_map.get(agent_id2, 0.0)
            new_value = max(-1.0, min(1.0, current + delta))
            self.agents[agent_id1].relationship_map[agent_id2] = new_value
    
    def get_scene_transcript(self, scene_id: str) -> list[dict[str, Any]]:
        """获取场景对话记录。"""
        if scene_id not in self.message_history:
            return []
        
        return [
            {
                "agent_name": self.agents[msg.from_agent].display_name if msg.from_agent in self.agents else "Unknown",
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in self.message_history[scene_id]
        ]
    
    async def cleanup_scene(self, scene_id: str) -> None:
        """清理场景资源。"""
        if scene_id in self.active_scenes:
            del self.active_scenes[scene_id]
        
        # 保留消息历史用于分析，但可以选择性清理
        logger.info(f"场景已清理: {scene_id}")


class SocialScenarioBuilder:
    """社交场景构建器 - 提供预定义的场景模板。"""
    
    @staticmethod
    def create_debate_scene(
        orchestrator: MultiAgentOrchestrator,
        topic: str,
        agent_ids: list[str],
    ) -> str:
        """创建辩论场景。"""
        return orchestrator.create_scene(
            name=f"辩论：{topic}",
            description=f"针对'{topic}'进行正反方辩论",
            interaction_type=InteractionType.DEBATE,
            participants=agent_ids,
            topic=topic,
            max_turns=10,
        )
    
    @staticmethod
    def create_casual_chat(
        orchestrator: MultiAgentOrchestrator,
        agent_ids: list[str],
    ) -> str:
        """创建闲聊场景。"""
        return orchestrator.create_scene(
            name="休闲聊天",
            description="多位AI在咖啡馆里闲聊",
            interaction_type=InteractionType.CASUAL_CHAT,
            participants=agent_ids,
            max_turns=15,
        )
    
    @staticmethod
    def create_teaching_scene(
        orchestrator: MultiAgentOrchestrator,
        teacher_id: str,
        student_ids: list[str],
        topic: str,
    ) -> str:
        """创建教学场景。"""
        all_participants = [teacher_id] + student_ids
        return orchestrator.create_scene(
            name=f"课程：{topic}",
            description=f"教师讲解{topic}，学生提问互动",
            interaction_type=InteractionType.TEACHING,
            participants=all_participants,
            topic=topic,
            max_turns=12,
        )
    
    @staticmethod
    def create_roleplay_scene(
        orchestrator: MultiAgentOrchestrator,
        scenario: str,
        agent_ids: list[str],
    ) -> str:
        """创建角色扮演场景。"""
        return orchestrator.create_scene(
            name=f"角色扮演：{scenario}",
            description=scenario,
            interaction_type=InteractionType.ROLEPLAY,
            participants=agent_ids,
            max_turns=20,
        )

