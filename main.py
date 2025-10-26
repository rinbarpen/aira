"""Aira 包的命令行入口。"""

from __future__ import annotations

from aira.server.cli import app

from dotenv import load_dotenv

def main() -> None:
    load_dotenv()
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
