"""CLI 入口。"""

from __future__ import annotations

import asyncio

import typer

from aira import get_version

app = typer.Typer(help="Aira 持续对话机器人 CLI")


@app.callback()
def main() -> None:
    """顶级 CLI 回调。"""


@app.command()
def version() -> None:
    """显示版本信息。"""
    typer.echo(get_version())


@app.command()
def chat(
    session: str = "default",
    persona: str = typer.Option("aira", "--persona", "-p", help="初始角色"),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="启用流式输出"),
) -> None:
    """开始交互式会话。
    
    支持特殊命令：
    - /switch <persona> : 切换角色（如 /switch tsundere）
    - /role <角色名> : 角色扮演（如 /role 猫娘）
    - /reset : 重置为初始角色
    - /help : 显示帮助
    """
    # 延迟导入，避免在模块加载时触发
    import sys
    from aira.core.config import ConfigWatcher, get_persona_config
    from aira.core.logging import setup_logging
    from aira.dialogue.orchestrator import DialogueContext, DialogueOrchestrator

    orchestrator = DialogueOrchestrator()
    watcher = ConfigWatcher()
    current_persona = persona
    initial_persona = persona
    role_play_mode = None  # 角色扮演模式
    
    typer.echo(f"启动会话：{session}")
    typer.echo(f"当前角色：{current_persona}")
    typer.echo(f"流式模式：{'开启' if stream else '关闭'}")
    typer.echo("")
    typer.secho("💡 特殊命令：", fg="cyan")
    typer.echo("  /switch <角色> - 切换预设角色")
    typer.echo("  /role <角色> - 角色扮演模式")
    typer.echo("  /reset - 重置角色")
    typer.echo("  /help - 帮助")
    typer.echo("")
    typer.echo("输入内容，Ctrl+C 结束。")
    typer.echo("")

    async def _loop() -> None:
        nonlocal current_persona, role_play_mode
        
        async with watcher:
            setup_logging("logs/aira.log")
            try:
                while True:
                    user_input = typer.prompt("你")
                    
                    # 处理特殊命令
                    if user_input.startswith("/"):
                        parts = user_input.split(maxsplit=1)
                        command = parts[0].lower()
                        
                        if command == "/help":
                            typer.secho("\n📖 可用命令：", fg="cyan", bold=True)
                            typer.echo("  /switch <角色> - 切换预设角色（aira, tsundere, cold等）")
                            typer.echo("  /role <角色> - 角色扮演（猫娘、女仆、老师等）")
                            typer.echo("  /reset - 重置为初始角色")
                            typer.echo("  /help - 显示此帮助\n")
                            continue
                        
                        elif command == "/switch":
                            if len(parts) < 2:
                                typer.secho("❌ 请指定角色：/switch <角色名>", fg="red")
                                continue
                            new_persona = parts[1]
                            try:
                                # 验证角色是否存在
                                get_persona_config(new_persona)
                                current_persona = new_persona
                                role_play_mode = None
                                typer.secho(f"✅ 已切换到：{new_persona}", fg="green")
                            except:
                                typer.secho(f"❌ 角色 '{new_persona}' 不存在", fg="red")
                            continue
                        
                        elif command == "/role":
                            if len(parts) < 2:
                                typer.secho("❌ 请指定角色：/role <角色名>", fg="red")
                                continue
                            role_play_mode = parts[1]
                            typer.secho(f"🎭 角色扮演模式：{role_play_mode}", fg="magenta")
                            typer.echo(f"   提示：AI 将扮演 {role_play_mode} 与你对话")
                            continue
                        
                        elif command == "/reset":
                            current_persona = initial_persona
                            role_play_mode = None
                            typer.secho(f"🔄 已重置为初始角色：{initial_persona}", fg="yellow")
                            continue
                        
                        else:
                            typer.secho(f"❌ 未知命令：{command}，输入 /help 查看帮助", fg="red")
                            continue
                    
                    # 构建上下文
                    metadata = {"request_id": "cli"}
                    
                    # 如果在角色扮演模式，添加到 metadata
                    if role_play_mode:
                        metadata["role_play"] = role_play_mode
                    
                    context = DialogueContext(
                        session_id=session,
                        persona_id=current_persona,
                        history=[],
                        metadata=metadata,
                    )
                    
                    if stream:
                        # 流式输出
                        typer.echo("艾拉: ", nl=False)
                        sys.stdout.flush()
                        
                        async for chunk in orchestrator.handle_turn_stream(context, user_input):
                            if chunk["type"] == "chunk":
                                typer.echo(chunk["content"], nl=False)
                                sys.stdout.flush()
                            elif chunk["type"] == "done":
                                typer.echo("")  # 换行
                                stats = chunk.get("stats", {})
                                if stats:
                                    typer.secho(
                                        f"[tokens: {stats.get('tokens_in', 0)}→{stats.get('tokens_out', 0)}, "
                                        f"耗时: {stats.get('duration', 0):.2f}s]",
                                        fg="green",
                                        dim=True
                                    )
                    else:
                        # 非流式输出
                        result = await orchestrator.handle_turn(context, user_input)
                        typer.echo(f"艾拉: {result['reply']}")
                        
                    typer.echo("")  # 空行分隔
                    
            except typer.Abort:
                typer.echo("\n会话终止。")
            except KeyboardInterrupt:
                typer.echo("\n会话终止。")

    asyncio.run(_loop())


@app.command()
def desktop() -> None:
    """启动桌面应用。"""
    try:
        from aira.desktop import run_desktop_app
        
        typer.echo("🚀 正在启动 AIRA 桌面应用...")
        typer.echo("提示：需要先安装桌面依赖 (uv sync --extra desktop)")
        typer.echo("")
        
        run_desktop_app()
    except ImportError as e:
        typer.echo(f"❌ 错误: 缺少桌面应用依赖", err=True)
        typer.echo(f"详情: {e}", err=True)
        typer.echo("")
        typer.echo("请运行以下命令安装桌面依赖：")
        typer.echo("  uv sync --extra desktop")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ 启动失败: {e}", err=True)
        raise typer.Exit(1)
