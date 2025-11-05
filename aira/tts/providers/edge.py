"""Microsoft Edge TTS提供商（免费）

Edge TTS是微软Edge浏览器使用的TTS服务，免费使用。
需要安装: pip install edge-tts
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from aira.tts.base import TTSProvider, TTSConfig, TTSResult


class EdgeTTSProvider(TTSProvider):
    """Microsoft Edge TTS提供商（免费）"""
    
    name = "edge"
    
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._audio_dir = Path("data/audio")
        self._audio_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查edge-tts是否安装
        if not shutil.which("edge-tts"):
            raise RuntimeError(
                "edge-tts 未安装。请运行: pip install edge-tts"
            )
    
    async def synthesize(self, text: str, config: TTSConfig) -> TTSResult:
        """使用Edge TTS合成语音"""
        self.validate_config(config)
        
        # 生成输出文件路径
        timestamp = int(time.time() * 1000)
        audio_path = self._audio_dir / f"edge_{timestamp}.mp3"
        
        # 构建命令
        cmd = [
            "edge-tts",
            "--text", text,
            "--voice", config.voice,
            "--write-media", str(audio_path)
        ]
        
        # 添加语速参数
        if config.speed != 1.0:
            # Edge TTS使用百分比格式，如 +50% 或 -50%
            rate_percent = int((config.speed - 1.0) * 100)
            cmd.extend(["--rate", f"{rate_percent:+d}%"])
        
        # 添加音量参数
        if config.volume != 1.0:
            volume_percent = int((config.volume - 1.0) * 100)
            cmd.extend(["--volume", f"{volume_percent:+d}%"])
        
        # 添加音调参数
        if config.pitch != 1.0:
            pitch_hz = int((config.pitch - 1.0) * 50)  # -50Hz to +50Hz
            cmd.extend(["--pitch", f"{pitch_hz:+d}Hz"])
        
        # 执行命令
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Edge TTS 执行失败: {e.stderr}") from e
        except Exception as e:
            raise RuntimeError(f"Edge TTS 错误: {e}") from e
        
        if not audio_path.exists():
            raise RuntimeError("Edge TTS 未生成音频文件")
        
        return TTSResult(
            provider=self.name,
            audio_path=audio_path,
            text=text,
            voice=config.voice
        )
    
    def get_available_voices(self) -> list[dict[str, Any]]:
        """获取Edge TTS可用的语音列表（部分常用）"""
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
                "description": "Warm and friendly"
            },
            # 日语语音
            {
                "id": "ja-JP-NanamiNeural",
                "name": "Nanami",
                "language": "ja-JP",
                "gender": "female",
                "description": "Natural Japanese female"
            },
            {
                "id": "ja-JP-KeitaNeural",
                "name": "Keita",
                "language": "ja-JP",
                "gender": "male",
                "description": "Natural Japanese male"
            },
        ]

