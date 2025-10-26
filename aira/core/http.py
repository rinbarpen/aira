from __future__ import annotations

import asyncio
from typing import Any

from curl_cffi import requests


class HTTPError(RuntimeError):
    def __init__(self, status_code: int, text: str) -> None:
        super().__init__(f"HTTP {status_code}: {text[:512]}")
        self.status_code = status_code
        self.text = text


def _post_json(url: str, *, headers: dict[str, str] | None = None, json: Any | None = None, timeout: int = 60) -> Any:
    resp = requests.post(url, headers=headers or {}, json=json, timeout=timeout)
    if resp.status_code >= 400:
        raise HTTPError(resp.status_code, resp.text)
    return resp.json()


async def post_json(url: str, *, headers: dict[str, str] | None = None, json: Any | None = None, timeout: int = 60) -> Any:
    return await asyncio.to_thread(_post_json, url, headers=headers, json=json, timeout=timeout)


