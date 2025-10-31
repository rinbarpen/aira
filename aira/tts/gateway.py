"""TTS网关 - 统一的TTS服务接口"""

from __future__ import annotations

import logging
from typing import Any

from aira.tts.base import TTSProvider, TTSConfig, TTSResult
from aira.tts.providers import (
    MinimaxTTSProvider,
    AzureTTSProvider,
    GoogleTTSProvider,
    EdgeTTSProvider,
)
from aira.tts.language_detector import LanguageDetector, VoiceSelector


logger = logging.getLogger(__name__)


class TTSGateway:
    """TTS网关 - 管理多个TTS提供商"""
    
    def __init__(self) -> None:
        """初始化TTS网关"""
        self._providers: dict[str, TTSProvider] = {}
        self._default_provider: str | None = None
        self._register_default_providers()
    
    def _register_default_providers(self) -> None:
        """注册默认的TTS提供商"""
        providers_to_register = [
            MinimaxTTSProvider,
            AzureTTSProvider,
            GoogleTTSProvider,
            EdgeTTSProvider,
        ]
        
        for provider_cls in providers_to_register:
            try:
                provider = provider_cls()
                self.register_provider(provider)
                logger.info(f"已注册TTS提供商: {provider.name}")
            except Exception as e:
                logger.warning(f"注册TTS提供商 {provider_cls.name} 失败: {e}")
    
    def register_provider(self, provider: TTSProvider) -> None:
        """注册TTS提供商
        
        Args:
            provider: TTS提供商实例
        """
        self._providers[provider.name] = provider
        
        # 如果是第一个提供商，设为默认
        if self._default_provider is None:
            self._default_provider = provider.name
    
    def set_default_provider(self, provider_name: str) -> None:
        """设置默认提供商
        
        Args:
            provider_name: 提供商名称
            
        Raises:
            ValueError: 提供商不存在
        """
        if provider_name not in self._providers:
            raise ValueError(f"TTS提供商 '{provider_name}' 不存在")
        self._default_provider = provider_name
    
    def get_provider(self, provider_name: str | None = None) -> TTSProvider:
        """获取TTS提供商
        
        Args:
            provider_name: 提供商名称，None表示使用默认
            
        Returns:
            TTS提供商实例
            
        Raises:
            ValueError: 提供商不存在
            RuntimeError: 没有可用的提供商
        """
        if provider_name is None:
            provider_name = self._default_provider
        
        if provider_name is None:
            raise RuntimeError("没有可用的TTS提供商")
        
        if provider_name not in self._providers:
            raise ValueError(f"TTS提供商 '{provider_name}' 不存在")
        
        return self._providers[provider_name]
    
    def list_providers(self) -> list[str]:
        """列出所有已注册的提供商
        
        Returns:
            提供商名称列表
        """
        return list(self._providers.keys())
    
    async def synthesize(
        self,
        text: str,
        provider: str | None = None,
        voice: str | None = None,
        config: TTSConfig | None = None,
        auto_detect_language: bool = True,
        preferred_language: str | None = None,
        auto_translate: bool = False,
        target_language: str | None = None,
        **kwargs: Any
    ) -> TTSResult:
        """合成语音（便捷方法）
        
        Args:
            text: 要转换的文本
            provider: 提供商名称，None使用默认
            voice: 语音名称（如果不指定，会根据文本语言自动选择）
            config: TTS配置，如果提供则忽略其他参数
            auto_detect_language: 是否自动检测语言并选择合适的语音
            preferred_language: 偏好的输出语言（zh, en, ja等）
            auto_translate: 是否启用自动翻译（当文本语言与目标语言不匹配时）
            target_language: 目标语言（用于翻译，如ja, en, zh等）
            **kwargs: 其他配置参数（language, speed, pitch, volume等）
            
        Returns:
            TTS结果
            
        Raises:
            ValueError: 参数错误
            RuntimeError: 合成失败
        """
        original_text = text
        
        # 自动翻译（如果需要）
        if auto_translate and target_language:
            # 检测源语言
            source_lang = self.detect_text_language(text)
            
            # 如果源语言与目标语言不同，进行翻译
            if source_lang != target_language:
                logger.info(
                    f"检测到语言不匹配: {source_lang} → {target_language}, "
                    f"启动翻译..."
                )
                
                try:
                    from aira.translation import get_translation_agent
                    
                    translator = get_translation_agent()
                    text = await translator.translate(
                        text=text,
                        target_language=target_language,
                        source_language=source_lang
                    )
                    
                    logger.info(
                        f"翻译完成: {original_text[:30]}... → {text[:30]}..."
                    )
                except Exception as e:
                    logger.error(f"翻译失败，使用原文: {e}")
                    # 翻译失败，继续使用原文
        
        # 获取提供商
        tts_provider = self.get_provider(provider)
        
        # 构建配置
        if config is None:
            # 智能语音选择
            if voice is None and auto_detect_language:
                # 自动检测语言并选择合适的语音
                voice, detected_lang = VoiceSelector.select_voice(
                    text=text,
                    provider=tts_provider.name,
                    preferred_language=preferred_language
                )
                lang_name = VoiceSelector.get_language_name(detected_lang)
                logger.info(
                    f"自动检测语言: {detected_lang} ({lang_name}), "
                    f"选择语音: {voice}"
                )
            elif voice is None:
                # 使用提供商的第一个可用语音
                available_voices = tts_provider.get_available_voices()
                if not available_voices:
                    raise ValueError(f"提供商 '{tts_provider.name}' 没有可用的语音")
                voice = available_voices[0]["id"]
            
            config = TTSConfig(
                provider=tts_provider.name,
                voice=voice,
                language=kwargs.get("language", "zh-CN"),
                speed=kwargs.get("speed", 1.0),
                pitch=kwargs.get("pitch", 1.0),
                volume=kwargs.get("volume", 1.0),
                format=kwargs.get("format", "mp3"),
                extra=kwargs.get("extra", {})
            )
        
        # 合成语音
        try:
            result = await tts_provider.synthesize(text, config)
            logger.info(
                f"TTS合成成功: provider={tts_provider.name}, "
                f"voice={config.voice}, file={result.audio_path}"
            )
            return result
        except Exception as e:
            logger.error(
                f"TTS合成失败: provider={tts_provider.name}, error={e}"
            )
            raise
    
    def detect_text_language(self, text: str) -> str:
        """检测文本的主要语言
        
        Args:
            text: 要检测的文本
            
        Returns:
            语言代码（zh, en, ja, ko等）
        """
        detector = LanguageDetector()
        return detector.detect_language(text)
    
    def detect_mixed_languages(self, text: str) -> dict[str, float]:
        """检测文本中各语言的比例
        
        Args:
            text: 要检测的文本
            
        Returns:
            各语言的比例字典
        """
        detector = LanguageDetector()
        return detector.detect_mixed_languages(text)
    
    def get_voices(self, provider: str | None = None) -> list[dict[str, Any]]:
        """获取可用的语音列表
        
        Args:
            provider: 提供商名称，None返回所有提供商的语音
            
        Returns:
            语音列表
        """
        if provider is not None:
            tts_provider = self.get_provider(provider)
            return tts_provider.get_available_voices()
        
        # 返回所有提供商的语音
        all_voices = []
        for prov in self._providers.values():
            voices = prov.get_available_voices()
            for voice in voices:
                voice["provider"] = prov.name
            all_voices.extend(voices)
        
        return all_voices


# 全局TTS网关实例
_global_gateway: TTSGateway | None = None


def get_tts_gateway() -> TTSGateway:
    """获取全局TTS网关实例
    
    Returns:
        TTS网关实例
    """
    global _global_gateway
    if _global_gateway is None:
        _global_gateway = TTSGateway()
    return _global_gateway

