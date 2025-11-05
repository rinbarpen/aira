"""TTS基础类和接口定义"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TTSConfig:
    """TTS配置"""
    provider: str  # minimax, azure, google, edge
    voice: str  # 语音名称
    language: str = "zh-CN"  # 语言代码
    speed: float = 1.0  # 语速 (0.5 - 2.0)
    pitch: float = 1.0  # 音调 (0.5 - 2.0)
    volume: float = 1.0  # 音量 (0.0 - 2.0)
    format: str = "mp3"  # 输出格式
    extra: dict[str, Any] = field(default_factory=dict)  # 额外参数


@dataclass
class TTSResult:
    """TTS结果"""
    provider: str  # 服务提供商
    audio_path: Path  # 音频文件路径
    duration: float | None = None  # 音频时长（秒）
    text: str = ""  # 原始文本
    voice: str = ""  # 使用的语音
    metadata: dict[str, Any] = field(default_factory=dict)  # 额外元数据


class TTSProvider(ABC):
    """TTS服务提供商抽象基类"""
    
    name: str = "base"
    
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """初始化TTS提供商
        
        Args:
            config: 提供商特定的配置
        """
        self._config = config or {}
    
    @abstractmethod
    async def synthesize(self, text: str, config: TTSConfig) -> TTSResult:
        """合成语音
        
        Args:
            text: 要转换的文本
            config: TTS配置
            
        Returns:
            TTS结果
            
        Raises:
            RuntimeError: 合成失败时抛出
        """
        pass
    
    @abstractmethod
    def get_available_voices(self) -> list[dict[str, Any]]:
        """获取可用的语音列表
        
        Returns:
            语音列表，每个语音包含 name, language, gender 等信息
        """
        pass
    
    def validate_config(self, config: TTSConfig) -> None:
        """验证配置是否有效
        
        Args:
            config: 要验证的配置
            
        Raises:
            ValueError: 配置无效时抛出
        """
        if not config.voice:
            raise ValueError(f"{self.name}: voice 不能为空")
        
        if not (0.5 <= config.speed <= 2.0):
            raise ValueError(f"{self.name}: speed 必须在 0.5-2.0 之间")
        
        if not (0.5 <= config.pitch <= 2.0):
            raise ValueError(f"{self.name}: pitch 必须在 0.5-2.0 之间")
        
        if not (0.0 <= config.volume <= 2.0):
            raise ValueError(f"{self.name}: volume 必须在 0.0-2.0 之间")

