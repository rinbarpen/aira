"""对话界面组件。"""

from __future__ import annotations

import asyncio
from typing import Any
from datetime import datetime

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
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QTextCursor, QColor

from aira.desktop.client import ApiClient


class MessageBubble(QFrame):
    """消息气泡组件。"""

    def __init__(self, message: str, is_user: bool = True, metadata: dict[str, Any] | None = None) -> None:
        """初始化消息气泡。
        
        Args:
            message: 消息内容
            is_user: 是否为用户消息
            metadata: 消息元数据
        """
        super().__init__()
        self.message = message
        self.is_user = is_user
        self.metadata = metadata or {}
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置界面。"""
        layout = QVBoxLayout(self)
        
        # 消息文本
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # 设置字体
        font = QFont()
        font.setPointSize(10)
        message_label.setFont(font)
        
        # 时间戳
        timestamp = datetime.now().strftime("%H:%M:%S")
        time_label = QLabel(timestamp)
        time_label.setStyleSheet("color: gray; font-size: 8pt;")
        
        layout.addWidget(message_label)
        layout.addWidget(time_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        # 设置样式
        if self.is_user:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #DCF8C6;
                    border-radius: 10px;
                    padding: 8px;
                    margin: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #FFFFFF;
                    border: 1px solid #E0E0E0;
                    border-radius: 10px;
                    padding: 8px;
                    margin: 4px;
                }
            """)
            
            # 如果有工具调用信息，显示
            if self.metadata.get("tools"):
                tools_info = QLabel(f"🔧 工具: {', '.join(t.get('tool', '') for t in self.metadata['tools'])}")
                tools_info.setStyleSheet("color: #666; font-size: 8pt; font-style: italic;")
                layout.addWidget(tools_info)


class ChatWidget(QWidget):
    """对话界面组件。"""

    def __init__(self, api_client: ApiClient) -> None:
        """初始化对话组件。
        
        Args:
            api_client: API 客户端实例
        """
        super().__init__()
        
        self.api_client = api_client
        self.session_id = "default"
        self.persona_id = "aira"
        self.conversation_history: list[dict[str, Any]] = []
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """设置用户界面。"""
        layout = QVBoxLayout(self)
        
        # 消息显示区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 消息容器
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.addStretch()
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area)
        
        # 输入区域
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入消息...")
        self.input_field.setMinimumHeight(40)
        
        self.send_button = QPushButton("发送")
        self.send_button.setMinimumSize(QSize(80, 40))
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # 清空对话按钮
        clear_layout = QHBoxLayout()
        self.clear_button = QPushButton("清空对话")
        self.clear_button.setMaximumWidth(100)
        clear_layout.addStretch()
        clear_layout.addWidget(self.clear_button)
        layout.addLayout(clear_layout)

    def _connect_signals(self) -> None:
        """连接信号和槽。"""
        self.send_button.clicked.connect(self._on_send_clicked)
        self.input_field.returnPressed.connect(self._on_send_clicked)
        self.clear_button.clicked.connect(self._on_clear_clicked)
        self.api_client.message_received.connect(self._on_message_received)

    def _on_send_clicked(self) -> None:
        """发送按钮点击处理。"""
        message = self.input_field.text().strip()
        if not message:
            return
        
        # 显示用户消息
        self._add_message(message, is_user=True)
        self.input_field.clear()
        
        # 禁用输入
        self.send_button.setEnabled(False)
        self.input_field.setEnabled(False)
        
        # 发送到后端
        asyncio.create_task(self._send_message(message))

    async def _send_message(self, message: str) -> None:
        """发送消息到后端。"""
        try:
            result = await self.api_client.send_message(
                message=message,
                session_id=self.session_id,
                persona_id=self.persona_id,
                history=self.conversation_history,
            )
            
            if result:
                # 更新对话历史
                self.conversation_history.append({"role": "user", "content": message})
                self.conversation_history.append({"role": "assistant", "content": result.get("reply", "")})
                
                # 保持历史记录不超过20轮
                if len(self.conversation_history) > 40:
                    self.conversation_history = self.conversation_history[-40:]
                    
        finally:
            # 重新启用输入
            self.send_button.setEnabled(True)
            self.input_field.setEnabled(True)
            self.input_field.setFocus()

    def _on_message_received(self, result: dict[str, Any]) -> None:
        """接收到消息响应。"""
        reply = result.get("reply", "")
        metadata = {
            "tools": result.get("tools", []),
            "memories": result.get("memories", []),
            "plan": result.get("plan", ""),
        }
        self._add_message(reply, is_user=False, metadata=metadata)

    def _add_message(self, message: str, is_user: bool = True, metadata: dict[str, Any] | None = None) -> None:
        """添加消息到显示区域。"""
        bubble = MessageBubble(message, is_user, metadata)
        
        # 移除最后的 stretch
        count = self.messages_layout.count()
        if count > 0:
            item = self.messages_layout.takeAt(count - 1)
            if item.spacerItem():
                pass  # stretch 已移除
        
        # 根据消息类型对齐
        if is_user:
            container = QHBoxLayout()
            container.addStretch()
            container.addWidget(bubble)
            self.messages_layout.addLayout(container)
        else:
            container = QHBoxLayout()
            container.addWidget(bubble)
            container.addStretch()
            self.messages_layout.addLayout(container)
        
        # 重新添加 stretch
        self.messages_layout.addStretch()
        
        # 滚动到底部
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_clear_clicked(self) -> None:
        """清空对话按钮点击处理。"""
        # 清空显示
        while self.messages_layout.count() > 0:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # 清理子布局中的部件
                sub_layout = item.layout()
                while sub_layout.count() > 0:
                    sub_item = sub_layout.takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()
        
        # 重新添加 stretch
        self.messages_layout.addStretch()
        
        # 清空历史记录
        self.conversation_history.clear()

