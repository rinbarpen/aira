"""ASR基础类和接口定义"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ASRConfig:
    """ASR配置"""
    provider: str  # whisper, azure, google, faster-whisper
    language: str | None = None  # 语言代码，如 zh, en, ja（None为自动检测）
    model: str = "base"  # 模型大小
    task: str = "transcribe"  # transcribe 或 translate（翻译为英文）
    temperature: float = 0.0  # 采样温度
    prompt: str | None = None  # 提示文本，提高准确性
    enable_timestamps: bool = False  # 是否返回时间戳
    enable_word_timestamps: bool = False  # 是否返回单词级时间戳
    extra: dict[str, Any] = field(default_factory=dict)  # 额外参数


@dataclass
class ASRSegment:
    """ASR片段（带时间戳）"""
    text: str
    start: float  # 开始时间（秒）
    end: float  # 结束时间（秒）
    confidence: float | None = None  # 置信度 (0.0-1.0)


@dataclass
class ASRResult:
    """ASR结果"""
    provider: str  # 服务提供商
    text: str  # 识别的文本
    language: str | None = None  # 检测到的语言
    duration: float | None = None  # 音频时长（秒）
    segments: list[ASRSegment] = field(default_factory=list)  # 片段（如果启用时间戳）
    confidence: float | None = None  # 整体置信度
    metadata: dict[str, Any] = field(default_factory=dict)  # 额外元数据


class ASRProvider(ABC):
    """ASR服务提供商抽象基类"""
    
    name: str = "base"
    
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """初始化ASR提供商
        
        Args:
            config: 提供商特定的配置
        """
        self._config = config or {}
    
    @abstractmethod
    async def transcribe(self, audio_path: Path, config: ASRConfig) -> ASRResult:
        """转录音频
        
        Args:
            audio_path: 音频文件路径
            config: ASR配置
            
        Returns:
            ASR结果
            
        Raises:
            RuntimeError: 转录失败时抛出
        """
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> list[dict[str, Any]]:
        """获取支持的语言列表
        
        Returns:
            语言列表，每个语言包含 code, name 等信息
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> list[str]:
        """获取支持的音频格式
        
        Returns:
            格式列表，如 ["mp3", "wav", "m4a", "ogg"]
        """
        pass
    
    def validate_config(self, config: ASRConfig) -> None:
        """验证配置是否有效
        
        Args:
            config: 要验证的配置
            
        Raises:
            ValueError: 配置无效时抛出
        """
        if config.task not in ["transcribe", "translate"]:
            raise ValueError(f"{self.name}: task 必须是 'transcribe' 或 'translate'")
        
        if not (0.0 <= config.temperature <= 1.0):
            raise ValueError(f"{self.name}: temperature 必须在 0.0-1.0 之间")
    
    def validate_audio_file(self, audio_path: Path) -> None:
        """验证音频文件是否有效
        
        Args:
            audio_path: 音频文件路径
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        file_extension = audio_path.suffix.lower().lstrip('.')
        supported_formats = self.get_supported_formats()
        
        if file_extension not in supported_formats:
            raise ValueError(
                f"{self.name}: 不支持的音频格式 '{file_extension}'. "
                f"支持的格式: {', '.join(supported_formats)}"
            )

