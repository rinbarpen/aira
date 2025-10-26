"""桌面应用主入口。"""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from aira.desktop.windows.main_window import MainWindow
from aira.core.logging import setup_logging


class DesktopApp:
    """桌面应用主类。"""

    def __init__(self) -> None:
        """初始化桌面应用。"""
        # 获取当前的 QApplication 实例（由 qasync 创建）
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
            
        self.app.setApplicationName("AIRA Desktop")
        self.app.setApplicationVersion("0.1.0")
        self.app.setOrganizationName("AIRA")
        
        # 设置应用图标（如果存在）
        icon_path = Path(__file__).parent / "resources" / "icon.png"
        if icon_path.exists():
            self.app.setWindowIcon(QIcon(str(icon_path)))
        
        # 初始化日志
        setup_logging("logs/aira_desktop.log", "INFO")
        
        # 创建主窗口
        self.main_window = MainWindow()

    def show(self) -> None:
        """显示主窗口。"""
        self.main_window.show()


def run_desktop_app() -> None:
    """运行桌面应用的便捷函数。"""
    from aira.desktop.main import main
    main()

