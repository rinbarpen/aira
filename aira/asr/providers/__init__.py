"""ASR服务提供商实现"""

from __future__ import annotations

from .whisper import WhisperASRProvider
from .azure import AzureASRProvider
from .google import GoogleASRProvider
from .faster_whisper import FasterWhisperASRProvider

__all__ = [
    "WhisperASRProvider",
    "AzureASRProvider",
    "GoogleASRProvider",
    "FasterWhisperASRProvider",
]

