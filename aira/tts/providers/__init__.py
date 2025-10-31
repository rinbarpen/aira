"""TTS服务提供商实现"""

from __future__ import annotations

from .minimax import MinimaxTTSProvider
from .azure import AzureTTSProvider
from .google import GoogleTTSProvider
from .edge import EdgeTTSProvider

__all__ = [
    "MinimaxTTSProvider",
    "AzureTTSProvider",
    "GoogleTTSProvider",
    "EdgeTTSProvider",
]

