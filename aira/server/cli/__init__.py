"""CLI 入口。"""

from __future__ import annotations

import asyncio

import typer

from aira import get_version
from aira.core.config import ConfigWatcher
from aira.core.logging import setup_logging
from aira.dialogue.orchestrator import DialogueContext, DialogueOrchestrator

app = typer.Typer(help="Aira 持续对话机器人 CLI")


@app.callback()
def main() -> None:
    """顶级 CLI 回调。"""


@app.command()
def version() -> None:
    typer.echo(get_version())


@app.command()
def chat(session: str = "default") -> None:
    """开始交互式会话。"""

    orchestrator = DialogueOrchestrator()
    watcher = ConfigWatcher()
    typer.echo(f"启动会话：{session}")
    typer.echo("输入内容，Ctrl+C 结束。")

    async def _loop() -> None:
        async with watcher:
            setup_logging("logs/aira.log")
            try:
                while True:
                    user_input = typer.prompt("你")
                    context = DialogueContext(
                        session_id=session,
                        persona_id="aira",
                        history=[],
                        metadata={"request_id": "cli"},
                    )
                    result = await orchestrator.handle_turn(context, user_input)
                    typer.echo(f"艾拉: {result['reply']}")
            except typer.Abort:
                typer.echo("会话终止。")

    asyncio.run(_loop())

