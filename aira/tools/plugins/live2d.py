from __future__ import annotations

import os
from typing import Any

from curl_cffi import requests


LIVE2D_ENDPOINT = os.environ.get("LIVE2D_ENDPOINT", "http://localhost:9876/live2d/action")


def perform_action(action: str, intensity: float = 1.0, emotion: str | None = None) -> dict[str, Any]:
    """向 Live2D 控制服务发送动作指令。"""

    payload: dict[str, Any] = {
        "action": action,
        "intensity": intensity,
    }
    if emotion:
        payload["emotion"] = emotion

    resp = requests.post(LIVE2D_ENDPOINT, json=payload, timeout=5)
    resp.raise_for_status()
    data = resp.json() if resp.content else {"status": "ok"}
    return {"requested": payload, "response": data}
