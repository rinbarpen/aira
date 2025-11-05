"""Microsoft Azure TTS提供商

Azure认知服务提供高质量的多语言TTS。
文档: https://learn.microsoft.com/azure/cognitive-services/speech-service/
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from curl_cffi import requests

from aira.tts.base import TTSProvider, TTSConfig, TTSResult


class AzureTTSProvider(TTSProvider):
    """Microsoft Azure TTS提供商"""
    
    name = "azure"
    
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._api_key = os.environ.get("AZURE_TTS_KEY")
        self._region = os.environ.get("AZURE_TTS_REGION", "eastus")
        self._endpoint = os.environ.get(
            "AZURE_TTS_ENDPOINT",
            f"https://{self._region}.tts.speech.microsoft.com/cognitiveservices/v1"
        )
        self._audio_dir = Path("data/audio")
        self._audio_dir.mkdir(parents=True, exist_ok=True)
    
    async def synthesize(self, text: str, config: TTSConfig) -> TTSResult:
        """使用Azure合成语音"""
        if not self._api_key:
            raise RuntimeError("AZURE_TTS_KEY 未设置")
        
        self.validate_config(config)
        
        # 计算速率百分比（Azure使用 -50% 到 +100% 格式）
        speed_percent = int((config.speed - 1.0) * 100)
        speed_str = f"{speed_percent:+d}%" if speed_percent != 0 else "0%"
        
        # 计算音调（Azure使用 -50% 到 +50% 格式）
        pitch_percent = int((config.pitch - 1.0) * 50)
        pitch_str = f"{pitch_percent:+d}%" if pitch_percent != 0 else "0%"
        
        # 计算音量（Azure使用 0% 到 100% 格式）
        volume_percent = int(config.volume * 50)  # 映射到0-100
        
        # 构建SSML
        ssml = config.extra.get("ssml")
        if not ssml:
            ssml = f"""<speak version='1.0' xml:lang='{config.language}'>
    <voice name='{config.voice}'>
        <prosody rate='{speed_str}' pitch='{pitch_str}' volume='{volume_percent}'>
            {text}
        </prosody>
    </voice>
</speak>"""
        
        # 输出格式
        output_format = config.extra.get(
            "format",
            "audio-24khz-96kbitrate-mono-mp3"
        )
        
        headers = {
            "Ocp-Apim-Subscription-Key": self._api_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": output_format,
            "User-Agent": "Aira"
        }
        
        # 发送请求
        try:
            resp = requests.post(
                self._endpoint,
                data=ssml.encode("utf-8"),
                headers=headers,
                timeout=30
            )
            resp.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Azure TTS 请求失败: {e}") from e
        
        # 保存音频文件
        timestamp = int(time.time() * 1000)
        audio_path = self._audio_dir / f"azure_{timestamp}.mp3"
        audio_path.write_bytes(resp.content)
        
        return TTSResult(
            provider=self.name,
            audio_path=audio_path,
            text=text,
            voice=config.voice,
            metadata={"format": output_format}
        )
    
    def get_available_voices(self) -> list[dict[str, Any]]:
        """获取Azure可用的语音列表（部分）"""
        return [
            # 中文语音
            {
                "id": "zh-CN-XiaoxiaoNeural",
                "name": "晓晓",
                "language": "zh-CN",
                "gender": "female",
                "description": "温暖明亮的女声"
            },
            {
                "id": "zh-CN-XiaoyiNeural",
                "name": "晓伊",
                "language": "zh-CN",
                "gender": "female",
                "description": "甜美可爱的女声"
            },
            {
                "id": "zh-CN-YunjianNeural",
                "name": "云健",
                "language": "zh-CN",
                "gender": "male",
                "description": "专业男声"
            },
            {
                "id": "zh-CN-YunxiNeural",
                "name": "云希",
                "language": "zh-CN",
                "gender": "male",
                "description": "沉稳男声"
            },
            {
                "id": "zh-CN-YunyangNeural",
                "name": "云扬",
                "language": "zh-CN",
                "gender": "male",
                "description": "专业新闻男声"
            },
            # 英文语音
            {
                "id": "en-US-AriaNeural",
                "name": "Aria",
                "language": "en-US",
                "gender": "female",
                "description": "Natural female voice"
            },
            {
                "id": "en-US-GuyNeural",
                "name": "Guy",
                "language": "en-US",
                "gender": "male",
                "description": "Natural male voice"
            },
            {
                "id": "en-US-JennyNeural",
                "name": "Jenny",
                "language": "en-US",
                "gender": "female",
                "description": "Warm and friendly female voice"
            },
            # 日语语音
            {
                "id": "ja-JP-NanamiNeural",
                "name": "Nanami",
                "language": "ja-JP",
                "gender": "female",
                "description": "Natural Japanese female voice"
            },
            {
                "id": "ja-JP-KeitaNeural",
                "name": "Keita",
                "language": "ja-JP",
                "gender": "male",
                "description": "Natural Japanese male voice"
            },
        ]

