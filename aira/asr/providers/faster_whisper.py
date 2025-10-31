"""Faster-Whisper ASR提供商（本地免费）

Faster-Whisper是Whisper的优化版本，可在本地运行。
GitHub: https://github.com/guillaumekln/faster-whisper
需要安装: pip install faster-whisper
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aira.asr.base import ASRProvider, ASRConfig, ASRResult, ASRSegment


class FasterWhisperASRProvider(ASRProvider):
    """Faster-Whisper ASR提供商（本地免费）"""
    
    name = "faster_whisper"
    
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._model = None
        self._model_size = None
    
    async def transcribe(self, audio_path: Path, config: ASRConfig) -> ASRResult:
        """使用Faster-Whisper转录音频"""
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise RuntimeError(
                "faster-whisper 未安装。请运行: pip install faster-whisper"
            )
        
        self.validate_config(config)
        self.validate_audio_file(audio_path)
        
        # 懒加载模型
        model_size = config.model or "base"
        if self._model is None or self._model_size != model_size:
            # 加载模型
            device = config.extra.get("device", "cpu")
            compute_type = config.extra.get("compute_type", "int8")
            
            self._model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type
            )
            self._model_size = model_size
        
        # 转录参数
        transcribe_params = {
            "language": config.language,
            "task": config.task,
            "beam_size": config.extra.get("beam_size", 5),
            "best_of": config.extra.get("best_of", 5),
            "temperature": config.temperature if config.temperature > 0 else 0.0,
            "word_timestamps": config.enable_word_timestamps,
        }
        
        if config.prompt:
            transcribe_params["initial_prompt"] = config.prompt
        
        # 执行转录
        try:
            segments_iter, info = self._model.transcribe(
                str(audio_path),
                **transcribe_params
            )
            
            # 收集所有片段
            segments_list = list(segments_iter)
            
            # 拼接文本
            text = " ".join([seg.text.strip() for seg in segments_list])
            
            # 构建片段列表
            segments = []
            if config.enable_timestamps:
                for seg in segments_list:
                    segments.append(ASRSegment(
                        text=seg.text.strip(),
                        start=seg.start,
                        end=seg.end,
                        confidence=seg.avg_logprob if hasattr(seg, 'avg_logprob') else None
                    ))
            
            return ASRResult(
                provider=self.name,
                text=text,
                language=info.language,
                duration=info.duration,
                segments=segments,
                confidence=info.language_probability,
                metadata={
                    "language_probability": info.language_probability,
                    "duration": info.duration,
                    "all_language_probs": info.all_language_probs,
                }
            )
            
        except Exception as e:
            raise RuntimeError(f"Faster-Whisper 转录失败: {e}") from e
    
    def get_supported_languages(self) -> list[dict[str, Any]]:
        """Faster-Whisper支持的语言（与Whisper相同）"""
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
            # 支持97+语言
        ]
    
    def get_supported_formats(self) -> list[str]:
        """Faster-Whisper支持的音频格式"""
        return ["mp3", "mp4", "m4a", "wav", "flac", "ogg", "opus", "webm"]
    
    def get_available_models(self) -> list[str]:
        """获取可用的模型大小"""
        return ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]

