"""多媒体处理模块。"""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

from PIL import Image
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import pyaudio
    import wave
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


class ImageHandler:
    """图像处理器。"""

    @staticmethod
    def load_image(file_path: str | Path) -> tuple[bytes, str]:
        """加载图像文件。
        
        Args:
            file_path: 图像文件路径
            
        Returns:
            (图像数据, MIME类型)
        """
        file_path = Path(file_path)
        img = Image.open(file_path)
        
        # 转换为RGB模式（如果需要）
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        
        # 压缩图像（如果太大）
        max_size = (1024, 1024)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 转换为字节
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        image_data = buffer.getvalue()
        
        return image_data, "image/jpeg"

    @staticmethod
    def image_to_data_uri(image_data: bytes, mime_type: str = "image/jpeg") -> str:
        """将图像数据转换为 data URI。
        
        Args:
            image_data: 图像字节数据
            mime_type: MIME类型
            
        Returns:
            data URI 字符串
        """
        b64_data = base64.b64encode(image_data).decode('utf-8')
        return f"data:{mime_type};base64,{b64_data}"

    @staticmethod
    def save_image(image_data: bytes, save_path: str | Path) -> None:
        """保存图像数据到文件。
        
        Args:
            image_data: 图像字节数据
            save_path: 保存路径
        """
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        img = Image.open(io.BytesIO(image_data))
        img.save(save_path)


class AudioRecorder(QObject):
    """音频录制器。"""
    
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal(str)  # 文件路径
    error_occurred = pyqtSignal(str)

    def __init__(self, output_dir: str = "data/audio") -> None:
        """初始化录音器。
        
        Args:
            output_dir: 输出目录
        """
        super().__init__()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.is_recording = False
        self.frames: list[bytes] = []
        self.stream = None
        self.audio = None
        
        if not AUDIO_AVAILABLE:
            raise RuntimeError("PyAudio not available. Install with: pip install pyaudio")

    def start_recording(self) -> None:
        """开始录音。"""
        if self.is_recording:
            return
        
        try:
            import pyaudio
            
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024,
            )
            
            self.is_recording = True
            self.frames = []
            self.recording_started.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"录音启动失败: {str(e)}")

    def stop_recording(self) -> str | None:
        """停止录音并保存文件。
        
        Returns:
            保存的文件路径
        """
        if not self.is_recording:
            return None
        
        try:
            self.is_recording = False
            
            # 读取剩余数据
            if self.stream:
                while True:
                    try:
                        data = self.stream.read(1024, exception_on_overflow=False)
                        self.frames.append(data)
                    except:
                        break
                
                self.stream.stop_stream()
                self.stream.close()
            
            if self.audio:
                self.audio.terminate()
            
            # 保存为WAV文件
            from datetime import datetime
            filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            filepath = self.output_dir / filename
            
            import wave
            with wave.open(str(filepath), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(16000)
                wf.writeframes(b''.join(self.frames))
            
            self.recording_stopped.emit(str(filepath))
            return str(filepath)
            
        except Exception as e:
            self.error_occurred.emit(f"录音保存失败: {str(e)}")
            return None

    def record_frame(self) -> None:
        """录制单个音频帧。"""
        if self.is_recording and self.stream:
            try:
                data = self.stream.read(1024, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                self.error_occurred.emit(f"录音错误: {str(e)}")


class WhisperASR(QObject):
    """Whisper 语音识别。"""
    
    transcription_completed = pyqtSignal(str)  # 识别文本
    error_occurred = pyqtSignal(str)

    def __init__(self, model_size: str = "base") -> None:
        """初始化 ASR。
        
        Args:
            model_size: 模型大小 (tiny/base/small/medium/large)
        """
        super().__init__()
        
        if not WHISPER_AVAILABLE:
            raise RuntimeError("faster-whisper not available. Install with: pip install faster-whisper")
        
        self.model_size = model_size
        self.model = None

    def load_model(self) -> None:
        """加载模型。"""
        try:
            if self.model is None:
                self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        except Exception as e:
            self.error_occurred.emit(f"模型加载失败: {str(e)}")

    def transcribe(self, audio_path: str, language: str | None = None) -> str:
        """转录音频文件。
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码（zh/en等）
            
        Returns:
            识别文本
        """
        try:
            if self.model is None:
                self.load_model()
            
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                beam_size=5
            )
            
            text = " ".join([segment.text for segment in segments])
            self.transcription_completed.emit(text)
            return text
            
        except Exception as e:
            error_msg = f"语音识别失败: {str(e)}"
            self.error_occurred.emit(error_msg)
            return ""


class AudioPlayer(QObject):
    """音频播放器。"""
    
    playback_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self) -> None:
        """初始化播放器。"""
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.mediaStatusChanged.connect(self._on_status_changed)

    def play(self, file_path: str) -> None:
        """播放音频文件。
        
        Args:
            file_path: 音频文件路径
        """
        try:
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.player.play()
        except Exception as e:
            self.error_occurred.emit(f"播放失败: {str(e)}")

    def stop(self) -> None:
        """停止播放。"""
        self.player.stop()

    def _on_status_changed(self, status) -> None:
        """播放状态变化处理。"""
        from PyQt6.QtMultimedia import QMediaPlayer
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.playback_finished.emit()


class DocumentHandler:
    """文档处理器。"""

    SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.doc', '.docx', '.md', '.json', '.xml'}

    @staticmethod
    def is_supported(file_path: str | Path) -> bool:
        """检查文件是否支持。
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持
        """
        return Path(file_path).suffix.lower() in DocumentHandler.SUPPORTED_EXTENSIONS

    @staticmethod
    def read_text_file(file_path: str | Path) -> str:
        """读取文本文件。
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
        """
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.txt':
            return file_path.read_text(encoding='utf-8')
        elif file_path.suffix.lower() == '.md':
            return file_path.read_text(encoding='utf-8')
        elif file_path.suffix.lower() == '.json':
            return file_path.read_text(encoding='utf-8')
        else:
            # 对于其他类型，返回文件信息
            return f"[文档] {file_path.name} ({file_path.stat().st_size} bytes)"

    @staticmethod
    def get_file_info(file_path: str | Path) -> dict[str, Any]:
        """获取文件信息。
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        file_path = Path(file_path)
        stat = file_path.stat()
        
        return {
            "name": file_path.name,
            "size": stat.st_size,
            "extension": file_path.suffix,
            "modified": stat.st_mtime,
        }

