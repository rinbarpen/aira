"""增强型对话界面组件，支持多媒体和高级功能。"""

from __future__ import annotations

import asyncio
from typing import Any
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QLabel,
    QFrame,
    QFileDialog,
    QComboBox,
    QCheckBox,
    QToolButton,
    QMenu,
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon

from aira.desktop.client import ApiClient
from aira.desktop.storage import ConversationStorage
from aira.desktop.media_handler import (
    ImageHandler,
    AudioRecorder,
    WhisperASR,
    AudioPlayer,
    DocumentHandler,
)
from aira.desktop.themes import ThemeManager


class MediaMessageBubble(QFrame):
    """支持多媒体的消息气泡。"""

    def __init__(
        self,
        message: str,
        is_user: bool = True,
        content_type: str = "text",
        media_path: str | None = None,
        metadata: dict[str, Any] | None = None,
        theme_manager: ThemeManager | None = None,
    ) -> None:
        super().__init__()
        self.message = message
        self.is_user = is_user
        self.content_type = content_type
        self.media_path = media_path
        self.metadata = metadata or {}
        self.theme_manager = theme_manager or ThemeManager()
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置界面。"""
        layout = QVBoxLayout(self)
        
        # 媒体内容
        if self.content_type == "image" and self.media_path:
            image_label = QLabel()
            pixmap = QPixmap(self.media_path)
            if not pixmap.isNull():
                # 缩放图片
                scaled_pixmap = pixmap.scaled(
                    300, 300,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                image_label.setPixmap(scaled_pixmap)
                layout.addWidget(image_label)
        
        elif self.content_type == "audio" and self.media_path:
            audio_label = QLabel(f"🎵 音频: {Path(self.media_path).name}")
            layout.addWidget(audio_label)
        
        elif self.content_type == "document" and self.media_path:
            doc_label = QLabel(f"📄 文档: {Path(self.media_path).name}")
            layout.addWidget(doc_label)
        
        # 文本消息
        if self.message:
            message_label = QLabel(self.message)
            message_label.setWordWrap(True)
            message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            
            font = QFont()
            font.setPointSize(10)
            message_label.setFont(font)
            
            layout.addWidget(message_label)
        
        # 时间戳
        timestamp = datetime.now().strftime("%H:%M:%S")
        time_label = QLabel(timestamp)
        time_label.setStyleSheet(f"color: {self.theme_manager.current_theme.text_secondary}; font-size: 8pt;")
        layout.addWidget(time_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        # 应用主题样式
        self.setStyleSheet(f"""
            MediaMessageBubble {{
                {self.theme_manager.get_bubble_style(self.is_user)}
            }}
        """)
        
        # 工具信息
        if not self.is_user and self.metadata.get("tools"):
            tools_info = QLabel(f"🔧 {', '.join(t.get('tool', '') for t in self.metadata['tools'])}")
            tools_info.setStyleSheet(f"color: {self.theme_manager.current_theme.text_secondary}; font-size: 8pt; font-style: italic;")
            layout.addWidget(tools_info)


class EnhancedChatWidget(QWidget):
    """增强型对话界面组件。"""

    def __init__(
        self,
        api_client: ApiClient,
        storage: ConversationStorage | None = None,
        theme_manager: ThemeManager | None = None,
    ) -> None:
        super().__init__()
        
        self.api_client = api_client
        self.storage = storage or ConversationStorage()
        self.theme_manager = theme_manager or ThemeManager()
        
        self.session_id = "default"
        self.persona_id = "aira"
        self.conversation_history: list[dict[str, Any]] = []
        
        # 多媒体处理器
        self.image_handler = ImageHandler()
        self.audio_recorder = AudioRecorder()
        self.audio_player = AudioPlayer()
        self.asr = None  # 延迟加载
        
        # 流式响应相关
        self.is_streaming = False
        self.current_stream_bubble = None
        self.stream_buffer = ""
        
        # 录音状态
        self.is_recording = False
        self.record_timer = QTimer()
        self.record_timer.timeout.connect(self._update_record_time)
        self.record_time = 0
        
        # 便捷回复
        self.quick_replies = [
            "继续", "详细说明", "简单点说", "举个例子",
            "换个话题", "总结一下", "有什么建议吗？"
        ]
        
        self._setup_ui()
        self._connect_signals()
        self._load_history()

    def _setup_ui(self) -> None:
        """设置用户界面。"""
        layout = QVBoxLayout(self)
        
        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        
        # 语言选择
        lang_label = QLabel("回复语言:")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["自动", "中文", "English", "日本語", "한국어"])
        self.language_map = {
            "自动": None,
            "中文": "zh",
            "English": "en",
            "日本語": "ja",
            "한국어": "ko",
        }
        
        # 流式响应开关
        self.stream_checkbox = QCheckBox("流式响应")
        self.stream_checkbox.setChecked(True)
        
        toolbar_layout.addWidget(lang_label)
        toolbar_layout.addWidget(self.language_combo)
        toolbar_layout.addWidget(self.stream_checkbox)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # 消息显示区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.addStretch()
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area)
        
        # 便捷回复按钮区域
        quick_reply_layout = QHBoxLayout()
        quick_reply_label = QLabel("快速回复:")
        quick_reply_layout.addWidget(quick_reply_label)
        
        for reply in self.quick_replies[:4]:  # 只显示前4个
            btn = QPushButton(reply)
            btn.setMaximumWidth(100)
            btn.clicked.connect(lambda checked, r=reply: self._on_quick_reply(r))
            quick_reply_layout.addWidget(btn)
        
        quick_reply_layout.addStretch()
        layout.addLayout(quick_reply_layout)
        
        # 输入区域
        input_layout = QHBoxLayout()
        
        # 多媒体按钮
        self.media_button = QToolButton()
        self.media_button.setText("📎")
        self.media_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        media_menu = QMenu(self)
        media_menu.addAction("📷 图片", self._on_upload_image)
        media_menu.addAction("🎤 录音", self._on_record_audio)
        media_menu.addAction("📄 文档", self._on_upload_document)
        self.media_button.setMenu(media_menu)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入消息...")
        self.input_field.setMinimumHeight(40)
        
        self.send_button = QPushButton("发送")
        self.send_button.setMinimumSize(QSize(80, 40))
        
        # 录音按钮
        self.record_button = QPushButton("🎤")
        self.record_button.setCheckable(True)
        self.record_button.setMinimumSize(QSize(40, 40))
        self.record_button.toggled.connect(self._on_record_toggle)
        
        input_layout.addWidget(self.media_button)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.record_button)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # 清空对话按钮
        clear_layout = QHBoxLayout()
        self.clear_button = QPushButton("清空对话")
        self.clear_button.setMaximumWidth(100)
        self.export_button = QPushButton("导出对话")
        self.export_button.setMaximumWidth(100)
        clear_layout.addStretch()
        clear_layout.addWidget(self.export_button)
        clear_layout.addWidget(self.clear_button)
        layout.addLayout(clear_layout)

    def _connect_signals(self) -> None:
        """连接信号和槽。"""
        self.send_button.clicked.connect(self._on_send_clicked)
        self.input_field.returnPressed.connect(self._on_send_clicked)
        self.clear_button.clicked.connect(self._on_clear_clicked)
        self.export_button.clicked.connect(self._on_export_clicked)
        
        self.api_client.message_received.connect(self._on_message_received)
        self.api_client.stream_chunk_received.connect(self._on_stream_chunk)
        
        self.audio_recorder.recording_stopped.connect(self._on_recording_stopped)

    def _load_history(self) -> None:
        """从本地存储加载历史。"""
        messages = self.storage.get_conversation(self.session_id, limit=50)
        for msg in messages:
            self._add_message_bubble(
                message=msg["content"],
                is_user=(msg["role"] == "user"),
                content_type=msg.get("content_type", "text"),
                metadata=msg.get("metadata", {}),
            )

    def _on_send_clicked(self) -> None:
        """发送按钮点击处理。"""
        message = self.input_field.text().strip()
        if not message:
            return
        
        # 显示用户消息
        self._add_message(message, is_user=True)
        self.input_field.clear()
        
        # 保存到本地
        self.storage.save_message(
            self.session_id,
            self.persona_id,
            "user",
            message,
            "text",
        )
        
        # 禁用输入
        self.send_button.setEnabled(False)
        self.input_field.setEnabled(False)
        
        # 发送到后端
        language = self.language_map[self.language_combo.currentText()]
        use_stream = self.stream_checkbox.isChecked()
        
        asyncio.create_task(self._send_message(message, use_stream, language))

    async def _send_message(self, message: str, stream: bool = False, language: str | None = None) -> None:
        """发送消息到后端。"""
        try:
            if stream:
                # 准备流式响应气泡
                self.is_streaming = True
                self.stream_buffer = ""
                self._add_streaming_bubble()
            
            result = await self.api_client.send_message(
                message=message,
                session_id=self.session_id,
                persona_id=self.persona_id,
                history=self.conversation_history[-20:] if self.conversation_history else [],
                stream=stream,
                language=language,
            )
            
            if result and not stream:
                # 非流式响应直接更新
                reply = result.get("reply", "")
                self.storage.save_message(
                    self.session_id,
                    self.persona_id,
                    "assistant",
                    reply,
                    "text",
                    result,
                )
                
                # 更新对话历史
                self.conversation_history.append({"role": "user", "content": message})
                self.conversation_history.append({"role": "assistant", "content": reply})
            
            elif stream:
                # 流式响应完成
                self.is_streaming = False
                if self.stream_buffer:
                    self.storage.save_message(
                        self.session_id,
                        self.persona_id,
                        "assistant",
                        self.stream_buffer,
                        "text",
                    )
                    self.conversation_history.append({"role": "user", "content": message})
                    self.conversation_history.append({"role": "assistant", "content": self.stream_buffer})
                    
        finally:
            # 重新启用输入
            self.send_button.setEnabled(True)
            self.input_field.setEnabled(True)
            self.input_field.setFocus()

    def _on_stream_chunk(self, chunk: str) -> None:
        """接收流式响应片段。"""
        if self.is_streaming and self.current_stream_bubble:
            self.stream_buffer += chunk
            # 更新气泡显示
            self._update_streaming_bubble(self.stream_buffer)

    def _add_streaming_bubble(self) -> None:
        """添加流式响应气泡。"""
        bubble = MediaMessageBubble("", False, "text", theme_manager=self.theme_manager)
        self.current_stream_bubble = bubble
        
        # 移除stretch
        count = self.messages_layout.count()
        if count > 0:
            self.messages_layout.takeAt(count - 1)
        
        container = QHBoxLayout()
        container.addWidget(bubble)
        container.addStretch()
        self.messages_layout.addLayout(container)
        self.messages_layout.addStretch()
        
        self._scroll_to_bottom()

    def _update_streaming_bubble(self, text: str) -> None:
        """更新流式响应气泡。"""
        if self.current_stream_bubble:
            # 找到气泡中的消息标签并更新
            for child in self.current_stream_bubble.findChildren(QLabel):
                if child.wordWrap():
                    child.setText(text)
                    break
            self._scroll_to_bottom()

    def _on_message_received(self, result: dict[str, Any]) -> None:
        """接收到消息响应（非流式）。"""
        if not self.is_streaming:  # 只处理非流式响应
            reply = result.get("reply", "")
            metadata = {
                "tools": result.get("tools", []),
                "memories": result.get("memories", []),
                "plan": result.get("plan", ""),
            }
            self._add_message(reply, is_user=False, metadata=metadata)

    def _add_message(
        self,
        message: str,
        is_user: bool = True,
        content_type: str = "text",
        media_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """添加消息到显示区域。"""
        self._add_message_bubble(message, is_user, content_type, media_path, metadata)

    def _add_message_bubble(
        self,
        message: str,
        is_user: bool,
        content_type: str = "text",
        media_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """添加消息气泡。"""
        bubble = MediaMessageBubble(
            message, is_user, content_type, media_path, metadata, self.theme_manager
        )
        
        # 移除最后的 stretch
        count = self.messages_layout.count()
        if count > 0:
            self.messages_layout.takeAt(count - 1)
        
        # 根据消息类型对齐
        container = QHBoxLayout()
        if is_user:
            container.addStretch()
            container.addWidget(bubble)
        else:
            container.addWidget(bubble)
            container.addStretch()
        
        self.messages_layout.addLayout(container)
        self.messages_layout.addStretch()
        
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        """滚动到底部。"""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_quick_reply(self, reply: str) -> None:
        """快速回复。"""
        self.input_field.setText(reply)
        self._on_send_clicked()

    def _on_upload_image(self) -> None:
        """上传图片。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            # 显示图片消息
            self._add_message(
                f"[图片] {Path(file_path).name}",
                is_user=True,
                content_type="image",
                media_path=file_path,
            )
            
            # 保存到本地
            self.storage.save_message(
                self.session_id,
                self.persona_id,
                "user",
                file_path,
                "image",
            )
            
            # TODO: 上传到后端
            asyncio.create_task(self._upload_and_send_file(file_path, "image"))

    def _on_record_audio(self) -> None:
        """录音。"""
        if not self.is_recording:
            self.is_recording = True
            self.record_time = 0
            self.audio_recorder.start_recording()
            self.record_timer.start(1000)
            self.record_button.setText(f"⏺ {self.record_time}s")
        else:
            self._stop_recording()

    def _on_record_toggle(self, checked: bool) -> None:
        """录音按钮切换。"""
        if checked:
            self._on_record_audio()
        else:
            if self.is_recording:
                self._stop_recording()

    def _stop_recording(self) -> None:
        """停止录音。"""
        self.is_recording = False
        self.record_timer.stop()
        self.record_button.setText("🎤")
        self.record_button.setChecked(False)
        self.audio_recorder.stop_recording()

    def _update_record_time(self) -> None:
        """更新录音时间。"""
        self.record_time += 1
        self.record_button.setText(f"⏺ {self.record_time}s")

    def _on_recording_stopped(self, file_path: str) -> None:
        """录音完成处理。"""
        # 显示音频消息
        self._add_message(
            f"[音频] {Path(file_path).name}",
            is_user=True,
            content_type="audio",
            media_path=file_path,
        )
        
        # 保存到本地
        self.storage.save_message(
            self.session_id,
            self.persona_id,
            "user",
            file_path,
            "audio",
        )
        
        # 语音识别
        asyncio.create_task(self._transcribe_and_send(file_path))

    async def _transcribe_and_send(self, audio_path: str) -> None:
        """转录并发送音频。"""
        try:
            if self.asr is None:
                from aira.desktop.media_handler import WhisperASR
                self.asr = WhisperASR("base")
            
            # 转录
            text = self.asr.transcribe(audio_path)
            if text:
                # 显示识别文本
                self.input_field.setText(text)
                # 自动发送
                self._on_send_clicked()
        except Exception as e:
            self.api_client.error_occurred.emit(f"语音识别失败: {str(e)}")

    def _on_upload_document(self) -> None:
        """上传文档。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文档", "", "文档文件 (*.txt *.pdf *.doc *.docx *.md *.json)"
        )
        if file_path:
            # 显示文档消息
            self._add_message(
                f"[文档] {Path(file_path).name}",
                is_user=True,
                content_type="document",
                media_path=file_path,
            )
            
            # 保存到本地
            self.storage.save_message(
                self.session_id,
                self.persona_id,
                "user",
                file_path,
                "document",
            )
            
            # TODO: 上传到后端
            asyncio.create_task(self._upload_and_send_file(file_path, "document"))

    async def _upload_and_send_file(self, file_path: str, file_type: str) -> None:
        """上传文件并发送。"""
        try:
            result = await self.api_client.upload_file(file_path, file_type)
            if result:
                # 文件上传成功，可以将URL作为消息发送
                pass
        except Exception as e:
            self.api_client.error_occurred.emit(f"文件上传失败: {str(e)}")

    def _on_clear_clicked(self) -> None:
        """清空对话。"""
        # 清空显示
        while self.messages_layout.count() > 0:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                sub_layout = item.layout()
                while sub_layout.count() > 0:
                    sub_item = sub_layout.takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()
        
        self.messages_layout.addStretch()
        
        # 清空历史记录
        self.conversation_history.clear()
        
        # 清空本地存储
        self.storage.delete_conversation(self.session_id)

    def _on_export_clicked(self) -> None:
        """导出对话。"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出对话", f"conversation_{self.session_id}.txt", "文本文件 (*.txt)"
        )
        if file_path:
            messages = self.storage.get_conversation(self.session_id)
            with open(file_path, "w", encoding="utf-8") as f:
                for msg in messages:
                    role = "用户" if msg["role"] == "user" else "助手"
                    f.write(f"[{msg['created_at']}] {role}: {msg['content']}\n\n")

    def apply_theme(self, theme_manager: ThemeManager) -> None:
        """应用主题。"""
        self.theme_manager = theme_manager
        # TODO: 重新渲染所有消息气泡

