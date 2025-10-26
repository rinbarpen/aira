from __future__ import annotations

import base64
import subprocess
from pathlib import Path
from typing import Any


MEDIA_DIR = Path("data/media")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def _run(command: list[str]) -> Path:
    output_path = MEDIA_DIR / f"capture_{len(list(MEDIA_DIR.iterdir()))}.png"
    subprocess.run(command + [str(output_path)], check=True)
    return output_path


def take_photo(device: str | None = None) -> dict[str, Any]:
    # 需要系统安装 fswebcam 或者使用其他命令；此处给出示例命令
    cmd = ["fswebcam", "--no-banner", "-r", "1280x720"]
    if device:
        cmd.extend(["-d", device])
    path = _run(cmd)
    return {"path": str(path), "data_uri": _to_data_uri(path)}


def grab_screenshot(display: str | None = None) -> dict[str, Any]:
    cmd = ["import", "-window", "root"]  # ImageMagick `import`
    if display:
        cmd.extend(["-display", display])
    path = _run(cmd)
    return {"path": str(path), "data_uri": _to_data_uri(path)}


def _to_data_uri(path: Path) -> str:
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


