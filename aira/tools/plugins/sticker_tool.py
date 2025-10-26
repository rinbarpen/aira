from __future__ import annotations

from pathlib import Path
from typing import Any

import json


STICKER_DB = {
    "happy": "https://cdn.example.com/stickers/happy.gif",
    "sad": "https://cdn.example.com/stickers/sad.gif",
    "cheer": "https://cdn.example.com/stickers/cheer.gif",
}


def get_sticker(mood: str = "happy", custom: str | None = None) -> dict[str, Any]:
    if custom and Path(custom).exists():
        url = Path(custom).as_uri()
    else:
        url = STICKER_DB.get(mood.lower(), STICKER_DB["happy"])
    return {"mood": mood, "url": url}


