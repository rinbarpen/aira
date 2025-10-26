"""配置加载与热更新支持。"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import json
from types import TracebackType
from typing import Any, Awaitable, Callable, Coroutine

import tomllib
from watchfiles import awatch

ChangeCallback = Callable[[dict[str, Any]], Awaitable[None] | None]


@dataclass
class _ConfigCacheEntry:
    data: dict[str, Any]
    mtime: float


class ConfigLoader:
    """加载并缓存 TOML 配置，支持热加载监听。"""

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir = base_dir or Path(__file__).resolve().parents[2]
        self._cache: dict[str, _ConfigCacheEntry] = {}
        self._subscribers: dict[str, list[ChangeCallback]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._watch_task: asyncio.Task[None] | None = None

    def load(self, relative_path: str, *, force: bool = False) -> dict[str, Any]:
        """加载配置；若文件更新则自动重载。"""

        path = self._base_dir / relative_path
        stat = path.stat()
        entry = self._cache.get(relative_path)
        if force or entry is None or stat.st_mtime > entry.mtime:
            with path.open("rb") as fp:
                data = tomllib.load(fp)
            new_entry = _ConfigCacheEntry(data=data, mtime=stat.st_mtime)
            self._cache[relative_path] = new_entry
            self._emit(relative_path, data)
            return data
        return entry.data

    def subscribe(self, relative_path: str, callback: ChangeCallback) -> None:
        """订阅配置变更通知。"""

        self._subscribers[relative_path].append(callback)

    async def ensure_watcher(self, *, poll_interval: float = 0.5) -> None:
        """启动后台监听任务，检测 `config` 目录下的文件变更。"""

        if self._watch_task and not self._watch_task.done():
            return

        async def _watch() -> None:
            config_dir = self._base_dir / "config"
            async for changes in awatch(config_dir, step=poll_interval):
                for _change, changed_path in changes:
                    try:
                        relative = changed_path.relative_to(self._base_dir).as_posix()
                    except ValueError:
                        continue
                    if relative in self._subscribers or relative in self._cache:
                        # 强制重载以触发通知
                        self.load(relative, force=True)

        self._watch_task = asyncio.create_task(_watch())

    async def stop_watcher(self) -> None:
        if self._watch_task and not self._watch_task.done():
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:  # pragma: no cover - 正常取消
                pass

    def _emit(self, relative_path: str, data: dict[str, Any]) -> None:
        callbacks = self._subscribers.get(relative_path)
        if not callbacks:
            return

        loop = self._get_loop()
        for callback in callbacks:
            result = callback(data)
            if asyncio.iscoroutine(result):
                loop.create_task(result)  # fire-and-forget

    @staticmethod
    def _get_loop() -> asyncio.AbstractEventLoop:
        try:
            return asyncio.get_running_loop()
        except RuntimeError:  # pragma: no cover - 在同步环境下可创建新 loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop


config_loader = ConfigLoader()


def get_app_config() -> dict[str, Any]:
    """获取全局应用配置。"""

    return config_loader.load("config/aira.toml")


def get_persona_config(persona_id: str) -> dict[str, Any]:
    """加载指定 persona 的配置。"""

    return config_loader.load(f"config/profiles/{persona_id}.toml")


def get_mcp_config() -> dict[str, Any]:
    base_dir = config_loader._base_dir  # noqa: SLF001
    json_path = base_dir / "config/mcp_servers.json"
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))
    cfg = config_loader.load("config/aira.toml").get("mcp", {})
    servers = cfg.get("servers", [])
    groups = cfg.get("groups", [])
    return {"servers": servers, "groups": groups}


class ConfigWatcher:
    """上下文管理器，用于在应用期间启用配置热加载。"""

    def __init__(self, loader: ConfigLoader | None = None) -> None:
        self._loader = loader or config_loader

    async def __aenter__(self) -> ConfigWatcher:
        await self._loader.ensure_watcher()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self._loader.stop_watcher()

