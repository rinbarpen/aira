#!/usr/bin/env python
"""启动增强版 AIRA 桌面应用。"""

from __future__ import annotations

import sys
import asyncio

from qasync import QEventLoop
from PyQt6.QtWidgets import QApplication

from dotenv import load_dotenv


def main() -> None:
    """启动桌面应用的主函数。"""
    # 加载环境变量
    load_dotenv()
    
    # 创建 Qt 应用
    app = QApplication(sys.argv)
    app.setApplicationName("AIRA Desktop Enhanced")
    app.setApplicationVersion("0.2.0")
    
    # 设置事件循环以支持异步
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # 导入并创建增强版主窗口
    from aira.desktop.windows.enhanced_main_window import EnhancedMainWindow
    
    main_window = EnhancedMainWindow()
    main_window.show()
    
    # 运行应用
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()

