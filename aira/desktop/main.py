"""桌面应用启动脚本。"""

from __future__ import annotations

import sys
import asyncio

from qasync import QEventLoop
from PyQt6.QtWidgets import QApplication

from aira.desktop.app import DesktopApp
from dotenv import load_dotenv


def main() -> None:
    """启动桌面应用的主函数。"""
    # 加载环境变量
    load_dotenv()
    
    # 创建 Qt 应用
    app = QApplication(sys.argv)
    
    # 设置事件循环以支持异步
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # 创建并显示主窗口
    desktop_app = DesktopApp()
    desktop_app.show()
    
    # 运行应用
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()

