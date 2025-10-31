"""Translation Agent模块

提供文本翻译功能，用于TTS语言转换。
"""

from __future__ import annotations

from .translator import TranslationAgent, get_translation_agent

__all__ = [
    "TranslationAgent",
    "get_translation_agent",
]

