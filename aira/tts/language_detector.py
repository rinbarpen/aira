"""TTS语言检测和智能语音选择

自动检测文本语言，并选择合适的TTS语音。
"""

from __future__ import annotations

import re
from typing import Any


class LanguageDetector:
    """简单的语言检测器"""
    
    @staticmethod
    def detect_language(text: str) -> str:
        """检测文本的主要语言
        
        Args:
            text: 要检测的文本
            
        Returns:
            语言代码（zh, en, ja, ko等）
        """
        if not text or not text.strip():
            return "en"
        
        # 计算各种字符的比例
        total_chars = len(text)
        
        # 中文字符（CJK统一汉字）
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0
        
        # 日文字符（平假名、片假名）
        japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
        japanese_ratio = japanese_chars / total_chars if total_chars > 0 else 0
        
        # 韩文字符
        korean_chars = len(re.findall(r'[\uac00-\ud7af]', text))
        korean_ratio = korean_chars / total_chars if total_chars > 0 else 0
        
        # 英文字符（ASCII字母）
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        english_ratio = english_chars / total_chars if total_chars > 0 else 0
        
        # 判断主要语言
        if chinese_ratio > 0.3:
            return "zh"
        elif japanese_ratio > 0.2:
            return "ja"
        elif korean_ratio > 0.2:
            return "ko"
        elif english_ratio > 0.5:
            return "en"
        elif chinese_ratio > 0.1:  # 混合中英文，中文占比较高
            return "zh"
        else:
            return "en"  # 默认英文
    
    @staticmethod
    def detect_mixed_languages(text: str) -> dict[str, float]:
        """检测文本中各语言的比例
        
        Args:
            text: 要检测的文本
            
        Returns:
            各语言的比例字典
        """
        if not text or not text.strip():
            return {"en": 1.0}
        
        total_chars = len(text)
        
        # 计算各语言字符数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
        korean_chars = len(re.findall(r'[\uac00-\ud7af]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        # 计算比例
        ratios = {
            "zh": chinese_chars / total_chars if total_chars > 0 else 0,
            "ja": japanese_chars / total_chars if total_chars > 0 else 0,
            "ko": korean_chars / total_chars if total_chars > 0 else 0,
            "en": english_chars / total_chars if total_chars > 0 else 0,
        }
        
        # 移除零比例的语言
        return {lang: ratio for lang, ratio in ratios.items() if ratio > 0}


class VoiceSelector:
    """智能语音选择器"""
    
    # 语言到语音的映射（各提供商的推荐语音）
    LANGUAGE_VOICE_MAP = {
        "edge": {
            "zh": "zh-CN-XiaoxiaoNeural",
            "en": "en-US-AriaNeural",
            "ja": "ja-JP-NanamiNeural",
            "ko": "ko-KR-SunHiNeural",
            "es": "es-ES-ElviraNeural",
            "fr": "fr-FR-DeniseNeural",
            "de": "de-DE-KatjaNeural",
            "ru": "ru-RU-SvetlanaNeural",
        },
        "minimax": {
            "zh": "female-shaonv",
            "en": "female-shaonv",  # Minimax主要支持中文
        },
        "azure": {
            "zh": "zh-CN-XiaoxiaoNeural",
            "en": "en-US-AriaNeural",
            "ja": "ja-JP-NanamiNeural",
            "ko": "ko-KR-SunHiNeural",
            "es": "es-ES-ElviraNeural",
            "fr": "fr-FR-DeniseNeural",
            "de": "de-DE-KatjaNeural",
            "ru": "ru-RU-SvetlanaNeural",
        },
        "google": {
            "zh": "cmn-CN-Wavenet-A",
            "en": "en-US-Wavenet-C",
            "ja": "ja-JP-Wavenet-A",
            "ko": "ko-KR-Wavenet-A",
            "es": "es-ES-Wavenet-C",
            "fr": "fr-FR-Wavenet-C",
            "de": "de-DE-Wavenet-C",
            "ru": "ru-RU-Wavenet-C",
        }
    }
    
    @classmethod
    def select_voice(
        cls,
        text: str,
        provider: str,
        preferred_language: str | None = None
    ) -> tuple[str, str]:
        """根据文本自动选择合适的语音
        
        Args:
            text: 要合成的文本
            provider: TTS提供商
            preferred_language: 用户偏好的语言（优先使用）
            
        Returns:
            (语音ID, 检测到的语言代码)
        """
        # 如果指定了偏好语言，使用偏好语言
        if preferred_language:
            language = preferred_language
        else:
            # 自动检测语言
            detector = LanguageDetector()
            language = detector.detect_language(text)
        
        # 获取该提供商的语音映射
        voice_map = cls.LANGUAGE_VOICE_MAP.get(provider, {})
        
        # 获取对应语言的语音，如果没有则使用默认
        voice = voice_map.get(language)
        
        if not voice:
            # 使用该提供商的第一个可用语音作为后备
            if voice_map:
                voice = next(iter(voice_map.values()))
            else:
                # 完全没有映射，返回通用默认值
                if provider == "edge":
                    voice = "zh-CN-XiaoxiaoNeural"
                elif provider == "minimax":
                    voice = "female-shaonv"
                elif provider == "azure":
                    voice = "zh-CN-XiaoxiaoNeural"
                elif provider == "google":
                    voice = "cmn-CN-Wavenet-A"
                else:
                    voice = "default"
        
        return voice, language
    
    @classmethod
    def get_language_name(cls, lang_code: str) -> str:
        """获取语言的显示名称
        
        Args:
            lang_code: 语言代码
            
        Returns:
            语言名称
        """
        names = {
            "zh": "中文",
            "en": "English",
            "ja": "日本語",
            "ko": "한국어",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch",
            "ru": "Русский",
        }
        return names.get(lang_code, lang_code)

