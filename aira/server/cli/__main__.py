"""CLI 入口点，允许使用 python -m aira.server.cli 运行。"""

from __future__ import annotations

from dotenv import load_dotenv

from aira.server.cli import app


if __name__ == "__main__":
    # 加载 .env 文件配置
    load_dotenv()
    app()

