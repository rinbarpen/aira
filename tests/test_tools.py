from __future__ import annotations

import pytest

from aira.tools.registry import ToolRegistry, ToolSpec


def test_register_local_tool() -> None:
    registry = ToolRegistry()

    def _tool(value: int) -> int:
        return value * 2

    spec = ToolSpec(id="double", entry="__main__:tool", callable=_tool)
    registry.register(spec)

    stored = registry.get("double")
    assert stored.callable is _tool

