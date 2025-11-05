"""Google Cloud TTS提供商

Google Cloud Text-to-Speech提供高质量的多语言TTS。
文档: https://cloud.google.com/text-to-speech/docs
"""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Any

from curl_cffi import requests

from aira.tts.base import TTSProvider, TTSConfig, TTSResult


class GoogleTTSProvider(TTSProvider):
    """Google Cloud TTS提供商"""
    
    name = "google"
    
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._api_key = os.environ.get("GOOGLE_CLOUD_API_KEY") or os.environ.get("GOOGLE_TTS_API_KEY")
        self._endpoint = os.environ.get(
            "GOOGLE_TTS_ENDPOINT",
            "https://texttospeech.googleapis.com/v1/text:synthesize"
        )
        self._audio_dir = Path("data/audio")
        self._audio_dir.mkdir(parents=True, exist_ok=True)
    
    async def synthesize(self, text: str, config: TTSConfig) -> TTSResult:
        """使用Google Cloud合成语音"""
        if not self._api_key:
            raise RuntimeError("GOOGLE_CLOUD_API_KEY 或 GOOGLE_TTS_API_KEY 未设置")
        
        self.validate_config(config)
        
        # 语言代码（从voice中提取，如 en-US-Wavenet-D -> en-US）
        language_code = config.language
        if "-" in config.voice:
            parts = config.voice.split("-")
            if len(parts) >= 2:
                language_code = f"{parts[0]}-{parts[1]}"
        
        # 构建请求
        payload = {
            "input": {"text": text},
            "voice": {
                "languageCode": language_code,
                "name": config.voice,
            },
            "audioConfig": {
                "audioEncoding": config.extra.get("encoding", "MP3"),
                "speakingRate": config.speed,
                "pitch": (config.pitch - 1.0) * 20,  # Google使用 -20.0 到 20.0
                "volumeGainDb": (config.volume - 1.0) * 16,  # Google使用 -96.0 到 16.0
                "sampleRateHertz": config.extra.get("sample_rate", 24000),
            }
        }
        
        # 添加效果（如果指定）
        if "effects" in config.extra:
            payload["audioConfig"]["effectsProfileId"] = config.extra["effects"]
        
        # 发送请求
        try:
            resp = requests.post(
                f"{self._endpoint}?key={self._api_key}",
                json=payload,
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise RuntimeError(f"Google TTS 请求失败: {e}") from e
        
        # 解析响应
        if "audioContent" not in data:
            raise RuntimeError(f"Google TTS 响应格式错误: {data}")
        
        audio_bytes = base64.b64decode(data["audioContent"])
        
        # 保存音频文件
        timestamp = int(time.time() * 1000)
        audio_path = self._audio_dir / f"google_{timestamp}.mp3"
        audio_path.write_bytes(audio_bytes)
        
        return TTSResult(
            provider=self.name,
            audio_path=audio_path,
            text=text,
            voice=config.voice,
            metadata=data
        )
    
    def get_available_voices(self) -> list[dict[str, Any]]:
        """获取Google可用的语音列表（部分）"""
        return [
            # 中文语音 (Mandarin)
            {
                "id": "cmn-CN-Wavenet-A",
                "name": "Wavenet-A (女性)",
                "language": "cmn-CN",
                "gender": "female",
                "description": "高质量中文女声"
            },
            {
                "id": "cmn-CN-Wavenet-B",
                "name": "Wavenet-B (男性)",
                "language": "cmn-CN",
                "gender": "male",
                "description": "高质量中文男声"
            },
            {
                "id": "cmn-CN-Wavenet-C",
                "name": "Wavenet-C (男性)",
                "language": "cmn-CN",
                "gender": "male",
                "description": "高质量中文男声"
            },
            {
                "id": "cmn-CN-Wavenet-D",
                "name": "Wavenet-D (女性)",
                "language": "cmn-CN",
                "gender": "female",
                "description": "高质量中文女声"
            },
            # 英文语音 (US)
            {
                "id": "en-US-Wavenet-A",
                "name": "Wavenet-A (Male)",
                "language": "en-US",
                "gender": "male",
                "description": "High quality US English male"
            },
            {
                "id": "en-US-Wavenet-C",
                "name": "Wavenet-C (Female)",
                "language": "en-US",
                "gender": "female",
                "description": "High quality US English female"
            },
            {
                "id": "en-US-Wavenet-D",
                "name": "Wavenet-D (Male)",
                "language": "en-US",
                "gender": "male",
                "description": "High quality US English male"
            },
            {
                "id": "en-US-Wavenet-F",
                "name": "Wavenet-F (Female)",
                "language": "en-US",
                "gender": "female",
                "description": "High quality US English female"
            },
            # 日语语音
            {
                "id": "ja-JP-Wavenet-A",
                "name": "Wavenet-A (女性)",
                "language": "ja-JP",
                "gender": "female",
                "description": "高品質な日本語女性"
            },
            {
                "id": "ja-JP-Wavenet-C",
                "name": "Wavenet-C (男性)",
                "language": "ja-JP",
                "gender": "male",
                "description": "高品質な日本語男性"
            },
        ]

