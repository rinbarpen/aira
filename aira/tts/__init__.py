"""Text-to-Speech (TTS) 模块

提供统一的TTS接口，支持多个服务提供商：
- Minimax TTS
- Microsoft Azure TTS
- Google Cloud TTS
- Edge TTS (免费)
"""

from __future__ import annotations

from .gateway import TTSGateway, get_tts_gateway
from .base import TTSProvider, TTSConfig, TTSResult

__all__ = [
    "TTSGateway",
    "get_tts_gateway",
    "TTSProvider",
    "TTSConfig",
    "TTSResult",
]

