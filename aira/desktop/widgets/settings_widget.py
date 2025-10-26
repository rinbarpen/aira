"""设置界面组件。"""

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
)
from PyQt6.QtCore import Qt

from aira.desktop.client import ApiClient


class SettingsWidget(QWidget):
    """设置界面组件。"""

    def __init__(self, api_client: ApiClient) -> None:
        """初始化设置组件。
        
        Args:
            api_client: API 客户端实例
        """
        super().__init__()
        
        self.api_client = api_client
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
        self.auto_save_check.setChecked(False)
        conversation_layout.addRow("自动保存对话:", self.auto_save_check)
        
        conversation_group.setLayout(conversation_layout)
        layout.addWidget(conversation_group)
        
        # 关于信息
        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout()
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setMaximumHeight(150)
        about_text.setPlainText(
            "AIRA Desktop v0.1.0\n\n"
            "可塑性记忆的持续对话机器人桌面前端\n\n"
            "支持多模型、持久记忆、角色扮演等功能\n"
            "基于 PyQt6 开发"
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
        
        button_layout.addStretch()
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

    def _on_reset(self) -> None:
        """恢复默认设置。"""
        self.api_url_input.setText("http://localhost:8000")
        self.font_size_spin.setValue(10)
        self.show_timestamp_check.setChecked(True)
        self.show_tools_check.setChecked(True)
        self.max_history_spin.setValue(40)
        self.auto_save_check.setChecked(False)

