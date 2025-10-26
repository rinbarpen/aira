from __future__ import annotations

import os
from typing import Any

from curl_cffi import requests

DEFAULT_SEARCH_ENDPOINT = os.environ.get("SEARCH_API_ENDPOINT", "https://api.scoutsearch.ai/v1/search")
DEFAULT_SEARCH_KEY = os.environ.get("SEARCH_API_KEY", "")


def web_search(query: str, *, limit: int = 5) -> dict[str, Any]:
    if not DEFAULT_SEARCH_KEY:
        raise RuntimeError("SEARCH_API_KEY 未设置，无法执行网络搜索")
    payload = {
        "query": query,
        "limit": limit,
    }
    headers = {
        "Authorization": f"Bearer {DEFAULT_SEARCH_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.post(DEFAULT_SEARCH_ENDPOINT, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()
