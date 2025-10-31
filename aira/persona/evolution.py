"""人格进化追踪器 - 根据交互历史动态调整人格特征。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from aira.core.config import get_app_config


@dataclass
class PersonaTrait:
    """人格特征定义。"""
    
    name: str  # 特征名称，如 warmth, humor, formality
    value: float  # 当前值 (0.0 - 1.0)
    baseline: float  # 基准值
    drift_rate: float = 0.01  # 漂移速率
    min_value: float = 0.0
    max_value: float = 1.0


@dataclass
class InteractionPattern:
    """交互模式统计。"""
    
    total_interactions: int = 0
    positive_feedback: int = 0  # 积极反馈次数
    negative_feedback: int = 0  # 消极反馈次数
    topics: dict[str, int] = field(default_factory=dict)  # 话题频率
    sentiment_history: list[float] = field(default_factory=list)  # 情感历史
    response_lengths: list[int] = field(default_factory=list)  # 回复长度
    emoji_usage: int = 0  # 表情符号使用次数
    formality_score: float = 0.5  # 正式程度评分
    last_updated: str = ""


class PersonaEvolutionTracker:
    """人格进化追踪器 - 根据用户交互动态调整AI人格。"""
    
    def __init__(self, persona_id: str, storage_dir: Path | None = None):
        self.persona_id = persona_id
        
        config = get_app_config()
        if storage_dir is None:
            storage_dir = Path(config.get("storage", {}).get("sqlite_path", "data/aira.db")).parent
        
        self.storage_dir = storage_dir
        self.evolution_file = self.storage_dir / f"evolution_{persona_id}.json"
        
        # 初始化人格特征
        self.traits: dict[str, PersonaTrait] = {
            "warmth": PersonaTrait(name="warmth", value=0.7, baseline=0.7),
            "humor": PersonaTrait(name="humor", value=0.5, baseline=0.5),
            "formality": PersonaTrait(name="formality", value=0.3, baseline=0.3),
            "enthusiasm": PersonaTrait(name="enthusiasm", value=0.6, baseline=0.6),
            "empathy": PersonaTrait(name="empathy", value=0.8, baseline=0.8),
            "curiosity": PersonaTrait(name="curiosity", value=0.7, baseline=0.7),
            "assertiveness": PersonaTrait(name="assertiveness", value=0.5, baseline=0.5),
        }
        
        # 交互模式统计
        self.pattern = InteractionPattern()
        
        # 加载已有的进化数据
        self._load_state()
    
    def _load_state(self) -> None:
        """从文件加载进化状态。"""
        if not self.evolution_file.exists():
            return
        
        try:
            with open(self.evolution_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 恢复特征值
            for trait_name, trait_data in data.get("traits", {}).items():
                if trait_name in self.traits:
                    self.traits[trait_name].value = trait_data["value"]
                    self.traits[trait_name].baseline = trait_data.get("baseline", trait_data["value"])
            
            # 恢复交互模式
            pattern_data = data.get("pattern", {})
            self.pattern = InteractionPattern(
                total_interactions=pattern_data.get("total_interactions", 0),
                positive_feedback=pattern_data.get("positive_feedback", 0),
                negative_feedback=pattern_data.get("negative_feedback", 0),
                topics=pattern_data.get("topics", {}),
                sentiment_history=pattern_data.get("sentiment_history", []),
                response_lengths=pattern_data.get("response_lengths", []),
                emoji_usage=pattern_data.get("emoji_usage", 0),
                formality_score=pattern_data.get("formality_score", 0.5),
                last_updated=pattern_data.get("last_updated", ""),
            )
        except Exception as e:
            print(f"加载人格进化状态失败: {e}")
    
    def _save_state(self) -> None:
        """保存进化状态到文件。"""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        data = {
            "persona_id": self.persona_id,
            "traits": {
                name: {
                    "value": trait.value,
                    "baseline": trait.baseline,
                    "drift_rate": trait.drift_rate,
                }
                for name, trait in self.traits.items()
            },
            "pattern": {
                "total_interactions": self.pattern.total_interactions,
                "positive_feedback": self.pattern.positive_feedback,
                "negative_feedback": self.pattern.negative_feedback,
                "topics": self.pattern.topics,
                "sentiment_history": self.pattern.sentiment_history[-100:],  # 只保留最近100条
                "response_lengths": self.pattern.response_lengths[-100:],
                "emoji_usage": self.pattern.emoji_usage,
                "formality_score": self.pattern.formality_score,
                "last_updated": datetime.now().isoformat(),
            },
            "last_saved": datetime.now().isoformat(),
        }
        
        with open(self.evolution_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def record_interaction(
        self,
        user_input: str,
        assistant_response: str,
        feedback: str | None = None,
        sentiment: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """记录一次交互并更新人格特征。
        
        Args:
            user_input: 用户输入
            assistant_response: AI回复
            feedback: 用户反馈 ("positive", "negative", None)
            sentiment: 情感得分 (-1.0 到 1.0)
            metadata: 额外元数据
        """
        metadata = metadata or {}
        
        self.pattern.total_interactions += 1
        self.pattern.sentiment_history.append(sentiment)
        self.pattern.response_lengths.append(len(assistant_response))
        
        # 统计表情符号使用
        emoji_count = sum(1 for char in assistant_response if ord(char) > 0x1F300)
        self.pattern.emoji_usage += emoji_count
        
        # 更新反馈统计
        if feedback == "positive":
            self.pattern.positive_feedback += 1
        elif feedback == "negative":
            self.pattern.negative_feedback += 1
        
        # 提取话题（简化版：基于关键词）
        topics = metadata.get("topics", [])
        for topic in topics:
            self.pattern.topics[topic] = self.pattern.topics.get(topic, 0) + 1
        
        # 根据交互模式调整人格特征
        self._evolve_traits()
        
        # 定期保存状态
        if self.pattern.total_interactions % 10 == 0:
            self._save_state()
    
    def _evolve_traits(self) -> None:
        """根据交互模式进化人格特征。"""
        if self.pattern.total_interactions < 5:
            return  # 至少需要5次交互才开始进化
        
        # 计算近期情感均值
        recent_sentiment = sum(self.pattern.sentiment_history[-20:]) / min(20, len(self.pattern.sentiment_history))
        
        # 计算反馈比率
        total_feedback = self.pattern.positive_feedback + self.pattern.negative_feedback
        positive_ratio = self.pattern.positive_feedback / total_feedback if total_feedback > 0 else 0.5
        
        # 1. 根据情感调整warmth
        if recent_sentiment > 0.3:
            self._adjust_trait("warmth", 0.02)  # 增加温暖度
        elif recent_sentiment < -0.3:
            self._adjust_trait("warmth", 0.03)  # 情感低落时更需要温暖
        
        # 2. 根据反馈调整humor
        if positive_ratio > 0.7:
            self._adjust_trait("humor", 0.015)  # 积极反馈多，可以更幽默
        elif positive_ratio < 0.3:
            self._adjust_trait("humor", -0.01)  # 反馈不好，减少幽默
        
        # 3. 根据表情符号使用调整enthusiasm
        avg_emoji_per_interaction = self.pattern.emoji_usage / max(1, self.pattern.total_interactions)
        if avg_emoji_per_interaction > 0.5:
            self._adjust_trait("enthusiasm", 0.01)
        
        # 4. 根据回复长度调整formality
        avg_response_length = sum(self.pattern.response_lengths[-20:]) / min(20, len(self.pattern.response_lengths))
        if avg_response_length > 200:
            self._adjust_trait("formality", 0.01)  # 长回复倾向正式
        elif avg_response_length < 50:
            self._adjust_trait("formality", -0.01)  # 短回复倾向随意
        
        # 5. 根据话题多样性调整curiosity
        topic_diversity = len(self.pattern.topics)
        if topic_diversity > 10:
            self._adjust_trait("curiosity", 0.02)
        
        # 6. 根据负面情感调整empathy
        if recent_sentiment < -0.2:
            self._adjust_trait("empathy", 0.025)  # 需要更多共情
    
    def _adjust_trait(self, trait_name: str, delta: float) -> None:
        """调整特定特征值。
        
        Args:
            trait_name: 特征名称
            delta: 变化量（正数增加，负数减少）
        """
        if trait_name not in self.traits:
            return
        
        trait = self.traits[trait_name]
        new_value = trait.value + delta
        
        # 限制在合理范围内
        trait.value = max(trait.min_value, min(trait.max_value, new_value))
    
    def get_personality_prompt(self) -> str:
        """生成当前人格状态的提示文本。"""
        prompts = []
        
        # 根据特征值生成描述
        if self.traits["warmth"].value > 0.7:
            prompts.append("你的语气温暖亲切")
        elif self.traits["warmth"].value < 0.3:
            prompts.append("你的语气相对中性客观")
        
        if self.traits["humor"].value > 0.6:
            prompts.append("适当使用幽默和俏皮的表达")
        
        if self.traits["formality"].value > 0.7:
            prompts.append("保持专业和正式的表达风格")
        elif self.traits["formality"].value < 0.3:
            prompts.append("使用轻松随意的表达方式")
        
        if self.traits["enthusiasm"].value > 0.7:
            prompts.append("展现出热情和活力")
        
        if self.traits["empathy"].value > 0.7:
            prompts.append("充分展现共情能力，理解和回应用户情感")
        
        if self.traits["curiosity"].value > 0.7:
            prompts.append("对新话题表现出好奇和探索欲")
        
        if self.traits["assertiveness"].value > 0.6:
            prompts.append("在需要时明确表达观点和建议")
        
        if not prompts:
            return ""
        
        return "【当前人格特征】\n" + "；".join(prompts) + "。"
    
    def get_evolution_summary(self) -> dict[str, Any]:
        """获取人格进化摘要。"""
        return {
            "persona_id": self.persona_id,
            "total_interactions": self.pattern.total_interactions,
            "traits": {
                name: {
                    "current": trait.value,
                    "baseline": trait.baseline,
                    "change": trait.value - trait.baseline,
                }
                for name, trait in self.traits.items()
            },
            "feedback_ratio": (
                self.pattern.positive_feedback / 
                max(1, self.pattern.positive_feedback + self.pattern.negative_feedback)
            ),
            "avg_sentiment": (
                sum(self.pattern.sentiment_history) / max(1, len(self.pattern.sentiment_history))
            ),
            "top_topics": sorted(
                self.pattern.topics.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5],
        }
    
    def reset_to_baseline(self) -> None:
        """重置所有特征到基准值。"""
        for trait in self.traits.values():
            trait.value = trait.baseline
        self._save_state()

