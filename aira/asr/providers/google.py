"""Google Cloud Speech-to-Text ASR提供商

Google Cloud提供高质量的语音识别服务。
文档: https://cloud.google.com/speech-to-text/docs
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from curl_cffi import requests

from aira.asr.base import ASRProvider, ASRConfig, ASRResult, ASRSegment


class GoogleASRProvider(ASRProvider):
    """Google Cloud Speech-to-Text ASR提供商"""
    
    name = "google_speech"
    
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._api_key = os.environ.get("GOOGLE_CLOUD_API_KEY") or os.environ.get("GOOGLE_SPEECH_API_KEY")
        self._endpoint = os.environ.get(
            "GOOGLE_SPEECH_ENDPOINT",
            "https://speech.googleapis.com/v1/speech:recognize"
        )
    
    async def transcribe(self, audio_path: Path, config: ASRConfig) -> ASRResult:
        """使用Google Speech转录音频"""
        if not self._api_key:
            raise RuntimeError("GOOGLE_CLOUD_API_KEY 或 GOOGLE_SPEECH_API_KEY 未设置")
        
        self.validate_config(config)
        self.validate_audio_file(audio_path)
        
        # 读取音频并编码
        audio_data = audio_path.read_bytes()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # 构建请求
        payload = {
            "config": {
                "encoding": self._get_encoding(audio_path),
                "sampleRateHertz": config.extra.get("sample_rate", 16000),
                "languageCode": config.language or "zh-CN",
                "enableWordTimeOffsets": config.enable_word_timestamps,
                "enableAutomaticPunctuation": True,
                "model": config.extra.get("model", "default"),
            },
            "audio": {
                "content": audio_base64
            }
        }
        
        # 添加可选参数
        if config.prompt:
            payload["config"]["speechContexts"] = [
                {"phrases": [config.prompt]}
            ]
        
        if config.enable_timestamps:
            payload["config"]["enableWordTimeOffsets"] = True
        
        # 发送请求
        try:
            resp = requests.post(
                f"{self._endpoint}?key={self._api_key}",
                json=payload,
                timeout=60
            )
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            raise RuntimeError(f"Google Speech ASR 请求失败: {e}") from e
        
        # 解析结果
        if "results" not in result or not result["results"]:
            return ASRResult(
                provider=self.name,
                text="",
                metadata=result
            )
        
        # 获取最佳识别结果
        alternatives = result["results"][0].get("alternatives", [])
        if not alternatives:
            return ASRResult(
                provider=self.name,
                text="",
                metadata=result
            )
        
        best = alternatives[0]
        text = best.get("transcript", "")
        confidence = best.get("confidence")
        
        # 解析单词时间戳
        segments = []
        if config.enable_word_timestamps and "words" in best:
            for word in best["words"]:
                start = float(word.get("startTime", "0s").rstrip('s'))
                end = float(word.get("endTime", "0s").rstrip('s'))
                segments.append(ASRSegment(
                    text=word.get("word", ""),
                    start=start,
                    end=end,
                    confidence=word.get("confidence")
                ))
        
        return ASRResult(
            provider=self.name,
            text=text,
            confidence=confidence,
            segments=segments,
            metadata=result
        )
    
    def get_supported_languages(self) -> list[dict[str, Any]]:
        """Google Speech支持的语言（部分）"""
        return [
            {"code": "cmn-Hans-CN", "name": "中文（简体）"},
            {"code": "cmn-Hant-TW", "name": "中文（繁體）"},
            {"code": "en-US", "name": "English (US)"},
            {"code": "en-GB", "name": "English (UK)"},
            {"code": "ja-JP", "name": "日本語"},
            {"code": "ko-KR", "name": "한국어"},
            {"code": "es-ES", "name": "Español"},
            {"code": "fr-FR", "name": "Français"},
            {"code": "de-DE", "name": "Deutsch"},
            {"code": "ru-RU", "name": "Русский"},
            # Google支持100+语言
        ]
    
    def get_supported_formats(self) -> list[str]:
        """Google Speech支持的音频格式"""
        return ["mp3", "wav", "flac", "ogg", "opus", "webm"]
    
    def _get_encoding(self, audio_path: Path) -> str:
        """获取Google Speech的编码格式"""
        ext = audio_path.suffix.lower()
        encodings = {
            ".mp3": "MP3",
            ".wav": "LINEAR16",
            ".flac": "FLAC",
            ".ogg": "OGG_OPUS",
            ".opus": "OGG_OPUS",
            ".webm": "WEBM_OPUS"
        }
        return encodings.get(ext, "LINEAR16")

