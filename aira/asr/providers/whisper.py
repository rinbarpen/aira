"""OpenAI Whisper ASR提供商

OpenAI的Whisper API提供高质量的语音识别。
文档: https://platform.openai.com/docs/guides/speech-to-text
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from curl_cffi import requests

from aira.asr.base import ASRProvider, ASRConfig, ASRResult, ASRSegment


class WhisperASRProvider(ASRProvider):
    """OpenAI Whisper ASR提供商"""
    
    name = "whisper"
    
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._api_key = os.environ.get("OPENAI_API_KEY")
        self._base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self._endpoint = f"{self._base_url}/audio/transcriptions"
    
    async def transcribe(self, audio_path: Path, config: ASRConfig) -> ASRResult:
        """使用Whisper转录音频"""
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY 未设置")
        
        self.validate_config(config)
        self.validate_audio_file(audio_path)
        
        # 构建请求
        headers = {
            "Authorization": f"Bearer {self._api_key}"
        }
        
        # 准备表单数据
        data = {
            "model": config.model if config.model in ["whisper-1"] else "whisper-1",
            "response_format": "verbose_json" if config.enable_timestamps else "json",
        }
        
        # 添加可选参数
        if config.language:
            data["language"] = config.language
        
        if config.prompt:
            data["prompt"] = config.prompt
        
        if config.temperature > 0:
            data["temperature"] = config.temperature
        
        if config.enable_timestamps:
            data["timestamp_granularities"] = ["segment"]
            if config.enable_word_timestamps:
                data["timestamp_granularities"].append("word")
        
        # 打开音频文件
        files = {
            "file": (audio_path.name, open(audio_path, "rb"), self._get_mime_type(audio_path))
        }
        
        # 发送请求
        try:
            resp = requests.post(
                self._endpoint,
                headers=headers,
                data=data,
                files=files,
                timeout=60
            )
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            raise RuntimeError(f"Whisper ASR 请求失败: {e}") from e
        finally:
            files["file"][1].close()
        
        # 解析结果
        text = result.get("text", "")
        language = result.get("language")
        duration = result.get("duration")
        
        # 解析片段
        segments = []
        if "segments" in result:
            for seg in result["segments"]:
                segments.append(ASRSegment(
                    text=seg.get("text", ""),
                    start=seg.get("start", 0.0),
                    end=seg.get("end", 0.0),
                    confidence=seg.get("confidence")
                ))
        
        return ASRResult(
            provider=self.name,
            text=text,
            language=language,
            duration=duration,
            segments=segments,
            metadata=result
        )
    
    def get_supported_languages(self) -> list[dict[str, Any]]:
        """Whisper支持的语言"""
        return [
            {"code": "zh", "name": "中文"},
            {"code": "en", "name": "English"},
            {"code": "ja", "name": "日本語"},
            {"code": "ko", "name": "한국어"},
            {"code": "es", "name": "Español"},
            {"code": "fr", "name": "Français"},
            {"code": "de", "name": "Deutsch"},
            {"code": "ru", "name": "Русский"},
            {"code": "ar", "name": "العربية"},
            {"code": "hi", "name": "हिन्दी"},
            # Whisper支持97+语言
        ]
    
    def get_supported_formats(self) -> list[str]:
        """Whisper支持的音频格式"""
        return ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
    
    def _get_mime_type(self, audio_path: Path) -> str:
        """获取音频文件的MIME类型"""
        ext = audio_path.suffix.lower()
        mime_types = {
            ".mp3": "audio/mpeg",
            ".mp4": "audio/mp4",
            ".m4a": "audio/m4a",
            ".wav": "audio/wav",
            ".webm": "audio/webm",
        }
        return mime_types.get(ext, "audio/mpeg")

