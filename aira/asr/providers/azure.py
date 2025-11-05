"""Microsoft Azure Speech ASR提供商

Azure认知服务提供高质量的语音识别。
文档: https://learn.microsoft.com/azure/cognitive-services/speech-service/
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any

from curl_cffi import requests

from aira.asr.base import ASRProvider, ASRConfig, ASRResult, ASRSegment


class AzureASRProvider(ASRProvider):
    """Microsoft Azure Speech ASR提供商"""
    
    name = "azure_speech"
    
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._api_key = os.environ.get("AZURE_SPEECH_KEY")
        self._region = os.environ.get("AZURE_SPEECH_REGION", "eastus")
        self._endpoint = f"https://{self._region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
    
    async def transcribe(self, audio_path: Path, config: ASRConfig) -> ASRResult:
        """使用Azure Speech转录音频"""
        if not self._api_key:
            raise RuntimeError("AZURE_SPEECH_KEY 未设置")
        
        self.validate_config(config)
        self.validate_audio_file(audio_path)
        
        # 构建请求参数
        params = {
            "language": config.language or "zh-CN",
            "format": "detailed" if config.enable_timestamps else "simple"
        }
        
        headers = {
            "Ocp-Apim-Subscription-Key": self._api_key,
            "Content-Type": self._get_content_type(audio_path)
        }
        
        # 读取音频数据
        audio_data = audio_path.read_bytes()
        
        # 发送请求
        try:
            resp = requests.post(
                self._endpoint,
                params=params,
                headers=headers,
                data=audio_data,
                timeout=60
            )
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            raise RuntimeError(f"Azure Speech ASR 请求失败: {e}") from e
        
        # 解析结果
        if params["format"] == "simple":
            text = result.get("DisplayText", "")
            segments = []
        else:
            # 详细格式
            nbest = result.get("NBest", [])
            if nbest:
                best = nbest[0]
                text = best.get("Display", "")
                
                # 解析单词级时间戳
                segments = []
                if config.enable_timestamps and "Words" in best:
                    for word in best["Words"]:
                        segments.append(ASRSegment(
                            text=word.get("Word", ""),
                            start=word.get("Offset", 0) / 10000000,  # 转换为秒
                            end=(word.get("Offset", 0) + word.get("Duration", 0)) / 10000000,
                            confidence=word.get("Confidence")
                        ))
            else:
                text = ""
                segments = []
        
        return ASRResult(
            provider=self.name,
            text=text,
            language=result.get("RecognitionStatus"),
            segments=segments,
            metadata=result
        )
    
    def get_supported_languages(self) -> list[dict[str, Any]]:
        """Azure Speech支持的语言（部分）"""
        return [
            {"code": "zh-CN", "name": "中文（简体）"},
            {"code": "zh-TW", "name": "中文（繁體）"},
            {"code": "en-US", "name": "English (US)"},
            {"code": "en-GB", "name": "English (UK)"},
            {"code": "ja-JP", "name": "日本語"},
            {"code": "ko-KR", "name": "한국어"},
            {"code": "es-ES", "name": "Español"},
            {"code": "fr-FR", "name": "Français"},
            {"code": "de-DE", "name": "Deutsch"},
            {"code": "ru-RU", "name": "Русский"},
            # Azure支持100+语言
        ]
    
    def get_supported_formats(self) -> list[str]:
        """Azure Speech支持的音频格式"""
        return ["wav", "mp3", "ogg", "opus", "webm"]
    
    def _get_content_type(self, audio_path: Path) -> str:
        """获取音频文件的Content-Type"""
        ext = audio_path.suffix.lower()
        content_types = {
            ".wav": "audio/wav; codecs=audio/pcm; samplerate=16000",
            ".mp3": "audio/mpeg",
            ".ogg": "audio/ogg; codecs=opus",
            ".opus": "audio/ogg; codecs=opus",
            ".webm": "audio/webm; codecs=opus"
        }
        return content_types.get(ext, "audio/wav")

