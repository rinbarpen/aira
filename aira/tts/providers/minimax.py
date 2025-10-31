"""Minimax TTS提供商

Minimax提供高质量的中文TTS服务。
文档: https://www.minimaxi.com/document/guides/speech-synthesis/overview
"""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Any

from curl_cffi import requests

from aira.tts.base import TTSProvider, TTSConfig, TTSResult


class MinimaxTTSProvider(TTSProvider):
    """Minimax TTS提供商"""
    
    name = "minimax"
    
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._api_key = os.environ.get("MINIMAX_API_KEY")
        self._group_id = os.environ.get("MINIMAX_GROUP_ID", "")
        self._endpoint = os.environ.get(
            "MINIMAX_TTS_ENDPOINT",
            "https://api.minimax.chat/v1/text_to_speech"
        )
        self._audio_dir = Path("data/audio")
        self._audio_dir.mkdir(parents=True, exist_ok=True)
    
    async def synthesize(self, text: str, config: TTSConfig) -> TTSResult:
        """使用Minimax合成语音"""
        if not self._api_key:
            raise RuntimeError("MINIMAX_API_KEY 未设置")
        
        self.validate_config(config)
        
        # 构建请求
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "model": config.extra.get("model", "speech-01"),
            "voice_id": config.voice,
            "speed": config.speed,
            "vol": config.volume,
            "pitch": config.pitch,
            "audio_sample_rate": config.extra.get("sample_rate", 24000),
            "bitrate": config.extra.get("bitrate", 128000),
        }
        
        # 添加group_id（如果配置了）
        if self._group_id:
            headers["GroupId"] = self._group_id
        
        # 发送请求
        try:
            resp = requests.post(
                self._endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise RuntimeError(f"Minimax TTS 请求失败: {e}") from e
        
        # 处理响应
        if "audio" in data:
            # Base64编码的音频数据
            audio_bytes = base64.b64decode(data["audio"])
        elif "audio_file" in data:
            # 音频文件URL
            audio_resp = requests.get(data["audio_file"], timeout=30)
            audio_resp.raise_for_status()
            audio_bytes = audio_resp.content
        else:
            raise RuntimeError(f"Minimax 响应格式错误: {data}")
        
        # 保存音频文件
        timestamp = int(time.time() * 1000)
        audio_path = self._audio_dir / f"minimax_{timestamp}.mp3"
        audio_path.write_bytes(audio_bytes)
        
        return TTSResult(
            provider=self.name,
            audio_path=audio_path,
            text=text,
            voice=config.voice,
            metadata=data
        )
    
    def get_available_voices(self) -> list[dict[str, Any]]:
        """获取Minimax可用的语音列表"""
        return [
            {
                "id": "male-qn-qingse",
                "name": "青涩青年音色",
                "language": "zh-CN",
                "gender": "male",
                "description": "适合有温度的知识讲解、亲切的话题互动"
            },
            {
                "id": "male-qn-jingying",
                "name": "精英青年音色",
                "language": "zh-CN",
                "gender": "male",
                "description": "适合专业领域的知识讲解和权威的角色身份"
            },
            {
                "id": "female-shaonv",
                "name": "少女音色",
                "language": "zh-CN",
                "gender": "female",
                "description": "适合可爱活泼的角色，或者甜美温柔的感觉"
            },
            {
                "id": "female-yujie",
                "name": "御姐音色",
                "language": "zh-CN",
                "gender": "female",
                "description": "适合成熟御姐的角色，或者温柔又有力量感的角色"
            },
            {
                "id": "presenter_male",
                "name": "男性主播",
                "language": "zh-CN",
                "gender": "male",
                "description": "适合新闻播报、有声阅读"
            },
            {
                "id": "presenter_female",
                "name": "女性主播",
                "language": "zh-CN",
                "gender": "female",
                "description": "适合新闻播报、有声阅读"
            },
            {
                "id": "audiobook_male_1",
                "name": "男性有声书1",
                "language": "zh-CN",
                "gender": "male",
                "description": "适合有声书朗读"
            },
            {
                "id": "audiobook_male_2",
                "name": "男性有声书2",
                "language": "zh-CN",
                "gender": "male",
                "description": "适合有声书朗读"
            },
            {
                "id": "audiobook_female_1",
                "name": "女性有声书1",
                "language": "zh-CN",
                "gender": "female",
                "description": "适合有声书朗读"
            },
            {
                "id": "audiobook_female_2",
                "name": "女性有声书2",
                "language": "zh-CN",
                "gender": "female",
                "description": "适合有声书朗读"
            },
        ]

