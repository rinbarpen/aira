"""Automatic Speech Recognition (ASR) 模块

提供统一的ASR接口，支持多个服务提供商：
- OpenAI Whisper API
- Microsoft Azure Speech
- Google Cloud Speech-to-Text
- Faster-Whisper (本地免费)
"""

from __future__ import annotations

from .gateway import ASRGateway, get_asr_gateway
from .base import ASRProvider, ASRConfig, ASRResult

__all__ = [
    "ASRGateway",
    "get_asr_gateway",
    "ASRProvider",
    "ASRConfig",
    "ASRResult",
]

