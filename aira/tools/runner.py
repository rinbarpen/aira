"""工具执行与 MCP 适配层。"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from aira.tools.registry import ToolRegistry, ToolSpec


class ToolExecutionError(Exception):
    """执行工具时发生的错误。"""


class ToolRunner:
    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self._registry = registry or ToolRegistry()
        self._http_client = httpx.AsyncClient(timeout=30)

    async def invoke(self, tool_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        spec = self._registry.get(tool_id)
        if spec.type == "local" and spec.callable:
            result = spec.callable(**payload)
            if asyncio.iscoroutine(result):
                result = await result
            return {"result": result}
        if spec.type == "mcp":
            return await self._invoke_mcp(spec, payload)
        raise ToolExecutionError(f"未知工具类型: {spec.type}")

    async def _invoke_mcp(self, spec: ToolSpec, payload: dict[str, Any]) -> dict[str, Any]:
        metadata = spec.metadata or {}
        url = metadata.get("url") or metadata.get("endpoint")
        token = metadata.get("token")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = await self._http_client.post(url, json={"tool": spec.id, "input": payload}, headers=headers)
        response.raise_for_status()
        return response.json()

