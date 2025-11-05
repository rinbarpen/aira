"""翻译Agent - 用于TTS语言转换

使用小模型（如gpt-4o-mini）快速翻译文本，
解决LLM输出语言与TTS目标语言不匹配的问题。
"""

from __future__ import annotations

import logging
from typing import Any

from aira.core.config import get_app_config


logger = logging.getLogger(__name__)


class TranslationAgent:
    """翻译Agent - 基于LLM的快速翻译"""
    
    def __init__(self, model: str | None = None) -> None:
        """初始化翻译Agent
        
        Args:
            model: 使用的模型（默认使用配置中的小模型）
        """
        self._config = get_app_config()
        
        # 获取翻译模型配置
        translation_config = self._config.get("translation", {})
        self._enabled = translation_config.get("enabled", True)
        self._model = model or translation_config.get("model", "openai:gpt-4o-mini")
        self._max_retries = translation_config.get("max_retries", 2)
        self._cache_enabled = translation_config.get("cache_enabled", True)
        
        # 简单的翻译缓存
        self._cache: dict[str, str] = {}
        
        # 懒加载模型网关
        self._gateway = None
    
    def _get_gateway(self):
        """懒加载模型网关"""
        if self._gateway is None:
            from aira.models import build_gateway
            self._gateway = build_gateway()
        return self._gateway
    
    def _get_cache_key(self, text: str, target_lang: str, source_lang: str | None) -> str:
        """生成缓存键"""
        source = source_lang or "auto"
        return f"{source}→{target_lang}:{text}"
    
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str | None = None,
        context: str | None = None
    ) -> str:
        """翻译文本
        
        Args:
            text: 要翻译的文本
            target_language: 目标语言（zh, en, ja, ko等）
            source_language: 源语言（None表示自动检测）
            context: 上下文信息，帮助更准确翻译
            
        Returns:
            翻译后的文本
            
        Raises:
            RuntimeError: 翻译失败
        """
        if not self._enabled:
            logger.warning("翻译Agent未启用，返回原文")
            return text
        
        if not text or not text.strip():
            return text
        
        # 检查缓存
        cache_key = self._get_cache_key(text, target_language, source_language)
        if self._cache_enabled and cache_key in self._cache:
            logger.info(f"使用缓存翻译: {text[:30]}...")
            return self._cache[cache_key]
        
        # 构建翻译提示
        prompt = self._build_translation_prompt(
            text, target_language, source_language, context
        )
        
        # 调用LLM翻译
        gateway = self._get_gateway()
        
        for attempt in range(self._max_retries):
            try:
                result = await gateway.generate(
                    name=self._model,
                    prompt=prompt,
                    temperature=0.3,  # 低温度保证稳定性
                    max_tokens=2000
                )
                
                translated_text = result.text.strip()
                
                # 移除可能的引号
                if translated_text.startswith('"') and translated_text.endswith('"'):
                    translated_text = translated_text[1:-1]
                if translated_text.startswith("'") and translated_text.endswith("'"):
                    translated_text = translated_text[1:-1]
                
                # 缓存结果
                if self._cache_enabled:
                    self._cache[cache_key] = translated_text
                
                logger.info(
                    f"翻译成功: {target_language} | "
                    f"原文: {text[:30]}... | "
                    f"译文: {translated_text[:30]}..."
                )
                
                return translated_text
                
            except Exception as e:
                logger.warning(f"翻译失败 (尝试 {attempt + 1}/{self._max_retries}): {e}")
                if attempt == self._max_retries - 1:
                    logger.error(f"翻译最终失败: {e}")
                    # 返回原文而不是抛出异常
                    return text
        
        return text
    
    def _build_translation_prompt(
        self,
        text: str,
        target_language: str,
        source_language: str | None,
        context: str | None
    ) -> str:
        """构建翻译提示"""
        # 语言名称映射
        lang_names = {
            "zh": "中文",
            "en": "English",
            "ja": "日本語",
            "ko": "한국어",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch",
            "ru": "Русский",
        }
        
        target_lang_name = lang_names.get(target_language, target_language)
        
        # 构建提示
        if source_language:
            source_lang_name = lang_names.get(source_language, source_language)
            prompt = f"Translate the following text from {source_lang_name} to {target_lang_name}."
        else:
            prompt = f"Translate the following text to {target_lang_name}."
        
        # 添加上下文
        if context:
            prompt += f"\n\nContext: {context}"
        
        prompt += "\n\nImportant guidelines:"
        prompt += "\n- Only output the translated text, nothing else"
        prompt += "\n- Maintain the tone and style of the original"
        prompt += "\n- Keep proper nouns and technical terms as appropriate"
        prompt += "\n- Ensure natural and fluent expression"
        
        prompt += f"\n\nText to translate:\n{text}"
        prompt += f"\n\nTranslation in {target_lang_name}:"
        
        return prompt
    
    async def batch_translate(
        self,
        texts: list[str],
        target_language: str,
        source_language: str | None = None
    ) -> list[str]:
        """批量翻译
        
        Args:
            texts: 文本列表
            target_language: 目标语言
            source_language: 源语言
            
        Returns:
            翻译后的文本列表
        """
        results = []
        for text in texts:
            translated = await self.translate(
                text=text,
                target_language=target_language,
                source_language=source_language
            )
            results.append(translated)
        return results
    
    def clear_cache(self) -> None:
        """清空翻译缓存"""
        self._cache.clear()
        logger.info("翻译缓存已清空")
    
    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)


# 全局翻译Agent实例
_global_agent: TranslationAgent | None = None


def get_translation_agent() -> TranslationAgent:
    """获取全局翻译Agent实例
    
    Returns:
        翻译Agent实例
    """
    global _global_agent
    if _global_agent is None:
        _global_agent = TranslationAgent()
    return _global_agent

