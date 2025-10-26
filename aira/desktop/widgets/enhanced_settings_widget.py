"""增强版设置界面组件。"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QCheckBox,
    QTextEdit,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from aira.desktop.client import ApiClient
from aira.desktop.themes import ThemeManager


class EnhancedSettingsWidget(QWidget):
    """增强版设置界面组件。"""
    
    # 定义信号
    theme_changed = pyqtSignal(str)  # 主题ID

    def __init__(
        self,
        api_client: ApiClient,
        theme_manager: ThemeManager | None = None,
    ) -> None:
        """初始化设置组件。
        
        Args:
            api_client: API 客户端实例
            theme_manager: 主题管理器
        """
        super().__init__()
        
        self.api_client = api_client
        self.theme_manager = theme_manager or ThemeManager()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置用户界面。"""
        layout = QVBoxLayout(self)
        
        # 连接设置
        connection_group = QGroupBox("连接设置")
        connection_layout = QFormLayout()
        
        self.api_url_input = QLineEdit()
        self.api_url_input.setText(self.api_client.base_url)
        self.api_url_input.setPlaceholderText("http://localhost:8000")
        
        connection_layout.addRow("API 地址:", self.api_url_input)
        
        update_url_button = QPushButton("更新连接")
        update_url_button.clicked.connect(self._on_update_url)
        connection_layout.addRow("", update_url_button)
        
        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)
        
        # 主题设置
        theme_group = QGroupBox("主题设置")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        theme_names = self.theme_manager.get_theme_display_names()
        for theme_id, theme_name in theme_names.items():
            self.theme_combo.addItem(theme_name, theme_id)
        
        theme_layout.addRow("当前主题:", self.theme_combo)
        
        apply_theme_button = QPushButton("应用主题")
        apply_theme_button.clicked.connect(self._on_apply_theme)
        theme_layout.addRow("", apply_theme_button)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # 显示设置
        display_group = QGroupBox("显示设置")
        display_layout = QFormLayout()
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(10)
        display_layout.addRow("字体大小:", self.font_size_spin)
        
        self.show_timestamp_check = QCheckBox()
        self.show_timestamp_check.setChecked(True)
        display_layout.addRow("显示时间戳:", self.show_timestamp_check)
        
        self.show_tools_check = QCheckBox()
        self.show_tools_check.setChecked(True)
        display_layout.addRow("显示工具调用:", self.show_tools_check)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # 对话设置
        conversation_group = QGroupBox("对话设置")
        conversation_layout = QFormLayout()
        
        self.max_history_spin = QSpinBox()
        self.max_history_spin.setRange(10, 100)
        self.max_history_spin.setValue(40)
        self.max_history_spin.setSingleStep(10)
        conversation_layout.addRow("最大历史记录:", self.max_history_spin)
        
        self.auto_save_check = QCheckBox()
        self.auto_save_check.setChecked(True)
        conversation_layout.addRow("自动保存对话:", self.auto_save_check)
        
        self.stream_default_check = QCheckBox()
        self.stream_default_check.setChecked(True)
        conversation_layout.addRow("默认启用流式响应:", self.stream_default_check)
        
        conversation_group.setLayout(conversation_layout)
        layout.addWidget(conversation_group)
        
        # 多媒体设置
        media_group = QGroupBox("多媒体设置")
        media_layout = QFormLayout()
        
        self.asr_model_combo = QComboBox()
        self.asr_model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self.asr_model_combo.setCurrentText("base")
        media_layout.addRow("ASR模型:", self.asr_model_combo)
        
        self.auto_transcribe_check = QCheckBox()
        self.auto_transcribe_check.setChecked(True)
        media_layout.addRow("自动转录语音:", self.auto_transcribe_check)
        
        self.image_quality_spin = QSpinBox()
        self.image_quality_spin.setRange(50, 100)
        self.image_quality_spin.setValue(85)
        media_layout.addRow("图片质量:", self.image_quality_spin)
        
        media_group.setLayout(media_layout)
        layout.addWidget(media_group)
        
        # 语言设置
        language_group = QGroupBox("语言设置")
        language_layout = QFormLayout()
        
        self.default_language_combo = QComboBox()
        self.default_language_combo.addItems(["自动", "中文", "English", "日本語", "한국어"])
        language_layout.addRow("默认回复语言:", self.default_language_combo)
        
        language_group.setLayout(language_layout)
        layout.addWidget(language_group)
        
        # 关于信息
        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout()
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setMaximumHeight(150)
        about_text.setPlainText(
            "AIRA Desktop v0.2.0 (增强版)\n\n"
            "可塑性记忆的持续对话机器人桌面前端\n\n"
            "新增功能:\n"
            "✨ 流式响应支持\n"
            "💾 对话历史本地存储\n"
            "🖼️ 图像、语音、文档支持\n"
            "🎤 ASR语音识别\n"
            "🎨 自定义主题系统\n"
            "⚡ 便捷回复功能\n"
            "🌍 多语言支持"
        )
        
        about_layout.addWidget(about_text)
        about_group.setLayout(about_layout)
        layout.addWidget(about_group)
        
        # 添加伸展空间
        layout.addStretch()
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        reset_button = QPushButton("恢复默认")
        reset_button.clicked.connect(self._on_reset)
        
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self._on_save)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(reset_button)
        
        layout.addLayout(button_layout)

    def _on_update_url(self) -> None:
        """更新 API 地址。"""
        new_url = self.api_url_input.text().strip()
        if new_url:
            self.api_client.base_url = new_url.rstrip("/")
            # 触发重新连接检查
            import asyncio
            asyncio.create_task(self.api_client.check_health())

    def _on_apply_theme(self) -> None:
        """应用主题。"""
        theme_id = self.theme_combo.currentData()
        if theme_id:
            self.theme_manager.set_theme(theme_id)
            self.theme_changed.emit(theme_id)

    def _on_save(self) -> None:
        """保存设置。"""
        # TODO: 将设置保存到配置文件
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "保存设置", "设置已保存")

    def _on_reset(self) -> None:
        """恢复默认设置。"""
        self.api_url_input.setText("http://localhost:8000")
        self.font_size_spin.setValue(10)
        self.show_timestamp_check.setChecked(True)
        self.show_tools_check.setChecked(True)
        self.max_history_spin.setValue(40)
        self.auto_save_check.setChecked(True)
        self.stream_default_check.setChecked(True)
        self.asr_model_combo.setCurrentText("base")
        self.auto_transcribe_check.setChecked(True)
        self.image_quality_spin.setValue(85)
        self.default_language_combo.setCurrentText("自动")

