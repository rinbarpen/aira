from __future__ import annotations

import pytest

from aira.server.api import create_app


@pytest.mark.asyncio
async def test_api_health() -> None:
    app = create_app()
    # 轻量验证可创建应用、存在路由
    routes = {r.path for r in app.router.routes}
    assert "/health" in routes

