"""ASR网关 - 统一的ASR服务接口"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from aira.asr.base import ASRProvider, ASRConfig, ASRResult
from aira.asr.providers import (
    WhisperASRProvider,
    AzureASRProvider,
    GoogleASRProvider,
    FasterWhisperASRProvider,
)


logger = logging.getLogger(__name__)


class ASRGateway:
    """ASR网关 - 管理多个ASR提供商"""
    
    def __init__(self) -> None:
        """初始化ASR网关"""
        self._providers: dict[str, ASRProvider] = {}
        self._default_provider: str | None = None
        self._register_default_providers()
    
    def _register_default_providers(self) -> None:
        """注册默认的ASR提供商"""
        providers_to_register = [
            WhisperASRProvider,
            AzureASRProvider,
            GoogleASRProvider,
            FasterWhisperASRProvider,
        ]
        
        for provider_cls in providers_to_register:
            try:
                provider = provider_cls()
                self.register_provider(provider)
                logger.info(f"已注册ASR提供商: {provider.name}")
            except Exception as e:
                logger.warning(f"注册ASR提供商 {provider_cls.name} 失败: {e}")
    
    def register_provider(self, provider: ASRProvider) -> None:
        """注册ASR提供商
        
        Args:
            provider: ASR提供商实例
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
            raise ValueError(f"ASR提供商 '{provider_name}' 不存在")
        self._default_provider = provider_name
    
    def get_provider(self, provider_name: str | None = None) -> ASRProvider:
        """获取ASR提供商
        
        Args:
            provider_name: 提供商名称，None表示使用默认
            
        Returns:
            ASR提供商实例
            
        Raises:
            ValueError: 提供商不存在
            RuntimeError: 没有可用的提供商
        """
        if provider_name is None:
            provider_name = self._default_provider
        
        if provider_name is None:
            raise RuntimeError("没有可用的ASR提供商")
        
        if provider_name not in self._providers:
            raise ValueError(f"ASR提供商 '{provider_name}' 不存在")
        
        return self._providers[provider_name]
    
    def list_providers(self) -> list[str]:
        """列出所有已注册的提供商
        
        Returns:
            提供商名称列表
        """
        return list(self._providers.keys())
    
    async def transcribe(
        self,
        audio_path: str | Path,
        provider: str | None = None,
        language: str | None = None,
        config: ASRConfig | None = None,
        **kwargs: Any
    ) -> ASRResult:
        """转录音频（便捷方法）
        
        Args:
            audio_path: 音频文件路径
            provider: 提供商名称，None使用默认
            language: 语言代码
            config: ASR配置，如果提供则忽略其他参数
            **kwargs: 其他配置参数
            
        Returns:
            ASR结果
            
        Raises:
            ValueError: 参数错误
            RuntimeError: 转录失败
        """
        # 获取提供商
        asr_provider = self.get_provider(provider)
        
        # 转换路径
        audio_path = Path(audio_path)
        
        # 构建配置
        if config is None:
            config = ASRConfig(
                provider=asr_provider.name,
                language=language,
                model=kwargs.get("model", "base"),
                task=kwargs.get("task", "transcribe"),
                temperature=kwargs.get("temperature", 0.0),
                prompt=kwargs.get("prompt"),
                enable_timestamps=kwargs.get("enable_timestamps", False),
                enable_word_timestamps=kwargs.get("enable_word_timestamps", False),
                extra=kwargs.get("extra", {})
            )
        
        # 转录音频
        try:
            result = await asr_provider.transcribe(audio_path, config)
            logger.info(
                f"ASR转录成功: provider={asr_provider.name}, "
                f"language={result.language}, text_length={len(result.text)}"
            )
            return result
        except Exception as e:
            logger.error(
                f"ASR转录失败: provider={asr_provider.name}, error={e}"
            )
            raise
    
    def get_supported_languages(self, provider: str | None = None) -> list[dict[str, Any]]:
        """获取支持的语言列表
        
        Args:
            provider: 提供商名称，None返回所有提供商的语言
            
        Returns:
            语言列表
        """
        if provider is not None:
            asr_provider = self.get_provider(provider)
            return asr_provider.get_supported_languages()
        
        # 返回所有提供商的语言
        all_languages: dict[str, dict[str, Any]] = {}
        for prov in self._providers.values():
            languages = prov.get_supported_languages()
            for lang in languages:
                code = lang["code"]
                if code not in all_languages:
                    all_languages[code] = lang
                    all_languages[code]["providers"] = []
                all_languages[code]["providers"].append(prov.name)
        
        return list(all_languages.values())
    
    def get_supported_formats(self, provider: str | None = None) -> list[str]:
        """获取支持的音频格式
        
        Args:
            provider: 提供商名称，None返回所有格式
            
        Returns:
            格式列表
        """
        if provider is not None:
            asr_provider = self.get_provider(provider)
            return asr_provider.get_supported_formats()
        
        # 返回所有提供商支持的格式（去重）
        all_formats = set()
        for prov in self._providers.values():
            all_formats.update(prov.get_supported_formats())
        
        return sorted(list(all_formats))


# 全局ASR网关实例
_global_gateway: ASRGateway | None = None


def get_asr_gateway() -> ASRGateway:
    """获取全局ASR网关实例
    
    Returns:
        ASR网关实例
    """
    global _global_gateway
    if _global_gateway is None:
        _global_gateway = ASRGateway()
    return _global_gateway

