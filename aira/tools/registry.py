"""工具与插件注册管理。"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Callable

from aira.core.config import get_app_config


ToolCallable = Callable[..., Any]


@dataclass
class ToolSpec:
    id: str
    entry: str
    callable: ToolCallable | None = None
    type: str = "local"
    metadata: dict[str, Any] | None = None


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._mcp_servers: dict[str, dict[str, Any]] = {}
        self._mcp_groups: dict[str, dict[str, Any]] = {}
        self._config = get_app_config()

    def clear(self) -> None:
        self._tools.clear()
        self._mcp_servers.clear()
        self._mcp_groups.clear()

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.id] = spec

    def register_from_config(
        self,
        configs: list[dict[str, Any]],
        *,
        mcp_config: dict[str, Any] | None = None,
    ) -> None:
        self.clear()
        if mcp_config:
            servers_cfg = mcp_config.get("servers", [])
            groups_cfg = mcp_config.get("groups", [])
            self._mcp_servers = {srv["id"]: srv for srv in servers_cfg}
            if isinstance(groups_cfg, dict):
                self._mcp_groups = groups_cfg
            else:
                self._mcp_groups = {g["id"]: g for g in groups_cfg}
        tts_enabled = self._config.get("tts", {}).get("enabled", True)
        for config in configs:
            metadata = {k: v for k, v in config.items() if k not in {"id", "entry", "type"}}
            if not tts_enabled and str(config["id"]).startswith("tts_"):
                continue
            spec = ToolSpec(
                id=config["id"],
                entry=config.get("entry", ""),
                type=config.get("type", "local"),
                metadata=metadata,
            )
            if spec.type == "local" and spec.entry:
                spec.callable = self._import_callable(spec.entry)
            elif spec.type == "mcp":
                server_id = metadata.get("mcp_server")
                if server_id and self._mcp_servers:
                    server_info = self._mcp_servers.get(server_id, {})
                    group_id = metadata.get("group")
                    if group_id:
                        group_cfg = self._mcp_groups.get(group_id, {})
                        enabled = group_cfg.get("enabled", True)
                        if not enabled:
                            continue
                    spec.metadata = {**server_info, **metadata}
            self.register(spec)

    def get(self, tool_id: str) -> ToolSpec:
        return self._tools[tool_id]

    def list(self) -> list[ToolSpec]:
        return list(self._tools.values())

    @staticmethod
    def _import_callable(entry: str) -> ToolCallable:
        module_name, attr = entry.split(":", 1)
        module = importlib.import_module(module_name)
        return getattr(module, attr)

