"""主窗口实现。"""

from __future__ import annotations

import asyncio
from typing import Any

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
    QComboBox,
    QStatusBar,
    QSplitter,
    QListWidget,
    QTabWidget,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor

from aira.desktop.client import ApiClient
from aira.desktop.widgets.chat_widget import ChatWidget
from aira.desktop.widgets.settings_widget import SettingsWidget


class MainWindow(QMainWindow):
    """AIRA 桌面应用主窗口。"""

    def __init__(self) -> None:
        """初始化主窗口。"""
        super().__init__()
        
        self.api_client = ApiClient()
        self.current_session_id = "default"
        self.current_persona_id = "aira"
        
        self._setup_ui()
        self._connect_signals()
        self._start_health_check()

    def _setup_ui(self) -> None:
        """设置用户界面。"""
        self.setWindowTitle("AIRA Desktop - AI 对话助手")
        self.setMinimumSize(1000, 700)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        
        # 会话选择
        session_label = QLabel("会话:")
        self.session_combo = QComboBox()
        self.session_combo.setEditable(True)
        self.session_combo.addItems(["default", "新会话"])
        self.session_combo.setCurrentText(self.current_session_id)
        
        # 角色选择
        persona_label = QLabel("角色:")
        self.persona_combo = QComboBox()
        self.persona_combo.addItems([
            "aira", "tsundere", "cold", "straight", 
            "dark", "ojousama", "king", "slave", 
            "otaku", "athlete"
        ])
        self.persona_combo.setCurrentText(self.current_persona_id)
        
        # 连接状态指示器
        self.connection_label = QLabel("⚫ 未连接")
        self.connection_label.setStyleSheet("color: red;")
        
        toolbar_layout.addWidget(session_label)
        toolbar_layout.addWidget(self.session_combo, 1)
        toolbar_layout.addWidget(persona_label)
        toolbar_layout.addWidget(self.persona_combo, 1)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.connection_label)
        
        main_layout.addLayout(toolbar_layout)
        
        # 选项卡
        self.tab_widget = QTabWidget()
        
        # 对话标签页
        self.chat_widget = ChatWidget(self.api_client)
        self.tab_widget.addTab(self.chat_widget, "对话")
        
        # 设置标签页
        self.settings_widget = SettingsWidget(self.api_client)
        self.tab_widget.addTab(self.settings_widget, "设置")
        
        main_layout.addWidget(self.tab_widget)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def _connect_signals(self) -> None:
        """连接信号和槽。"""
        self.session_combo.currentTextChanged.connect(self._on_session_changed)
        self.persona_combo.currentTextChanged.connect(self._on_persona_changed)
        self.api_client.connection_status_changed.connect(self._on_connection_status_changed)
        self.api_client.error_occurred.connect(self._on_error)
        
        # 将会话和角色信息传递给聊天组件
        self.chat_widget.session_id = self.current_session_id
        self.chat_widget.persona_id = self.current_persona_id

    def _start_health_check(self) -> None:
        """启动健康检查定时器。"""
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self._check_health)
        self.health_check_timer.start(5000)  # 每5秒检查一次
        
        # 立即执行一次检查
        self._check_health()

    def _check_health(self) -> None:
        """检查后端健康状态。"""
        asyncio.create_task(self.api_client.check_health())

    def _on_session_changed(self, session_id: str) -> None:
        """会话变更处理。"""
        if session_id == "新会话":
            import uuid
            new_session = f"session_{uuid.uuid4().hex[:8]}"
            self.session_combo.setCurrentText(new_session)
            self.session_combo.addItem(new_session)
            self.current_session_id = new_session
        else:
            self.current_session_id = session_id
        
        self.chat_widget.session_id = self.current_session_id
        self.status_bar.showMessage(f"切换到会话: {self.current_session_id}")

    def _on_persona_changed(self, persona_id: str) -> None:
        """角色变更处理。"""
        self.current_persona_id = persona_id
        self.chat_widget.persona_id = self.current_persona_id
        self.status_bar.showMessage(f"切换到角色: {self.current_persona_id}")

    def _on_connection_status_changed(self, connected: bool) -> None:
        """连接状态变更处理。"""
        if connected:
            self.connection_label.setText("🟢 已连接")
            self.connection_label.setStyleSheet("color: green;")
            self.status_bar.showMessage("已连接到后端服务")
        else:
            self.connection_label.setText("🔴 未连接")
            self.connection_label.setStyleSheet("color: red;")
            self.status_bar.showMessage("未连接到后端服务，请启动后端")

    def _on_error(self, error_msg: str) -> None:
        """错误处理。"""
        self.status_bar.showMessage(f"错误: {error_msg}")
        QMessageBox.warning(self, "错误", error_msg)

    def closeEvent(self, event) -> None:
        """关闭事件处理。"""
        self.health_check_timer.stop()
        asyncio.create_task(self.api_client.close())
        event.accept()

