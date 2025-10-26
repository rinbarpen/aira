from __future__ import annotations

import base64
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from curl_cffi import requests

AUDIO_DIR = Path("data/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def _save_audio(provider: str, data: bytes, suffix: str = ".mp3") -> Path:
    path = AUDIO_DIR / f"{provider}_{int(time.time()*1000)}{suffix}"
    path.write_bytes(data)
    return path


def _handle_json_audio(provider: str, response: dict[str, Any]) -> Path:
    if "audio_base64" in response:
        audio_bytes = base64.b64decode(response["audio_base64"])
        return _save_audio(provider, audio_bytes)
    if "audio_url" in response:
        resp = requests.get(response["audio_url"], timeout=30)
        resp.raise_for_status()
        return _save_audio(provider, resp.content)
    raise RuntimeError(f"{provider} 返回中缺少音频字段: {response}")


async def tts_minimax(text: str, voice: str = "alloy", **kwargs: Any) -> dict[str, Any]:
    endpoint = os.environ.get("MINIMAX_TTS_ENDPOINT", "https://api.minimax.chat/v1/tts")
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        raise RuntimeError("MINIMAX_API_KEY 未配置")
    payload = {
        "text": text,
        "voice": voice,
        **kwargs,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(endpoint, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    path = _handle_json_audio("minimax", data)
    return {"provider": "minimax", "path": str(path), "meta": data}


async def tts_edgetts(text: str, voice: str = "zh-CN-XiaoxiaoNeural", **kwargs: Any) -> dict[str, Any]:
    command = shutil.which("edge-tts")
    if not command:
        raise RuntimeError("未找到 edge-tts 命令，请先安装 edge-tts")
    path = AUDIO_DIR / f"edgetts_{int(time.time()*1000)}.mp3"
    cmd = [command, "--text", text, "--write-media", str(path), "--voice", voice]
    if "rate" in kwargs:
        cmd.extend(["--rate", str(kwargs["rate"])])
    subprocess.run(cmd, check=True)
    return {"provider": "edgetts", "path": str(path)}


async def tts_google(text: str, voice: str = "en-US-Wavenet-D", **kwargs: Any) -> dict[str, Any]:
    endpoint = os.environ.get("GOOGLE_TTS_ENDPOINT")
    api_key = os.environ.get("GOOGLE_TTS_API_KEY")
    if not endpoint or not api_key:
        raise RuntimeError("GOOGLE_TTS_ENDPOINT 或 GOOGLE_TTS_API_KEY 未配置")
    payload = {
        "input": {"text": text},
        "voice": {"name": voice, "languageCode": kwargs.get("language_code", voice[:5])},
        "audioConfig": {"audioEncoding": "MP3"},
    }
    resp = requests.post(f"{endpoint}?key={api_key}", json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "audioContent" not in data:
        raise RuntimeError(f"Google TTS 响应异常: {data}")
    audio_bytes = base64.b64decode(data["audioContent"])
    path = _save_audio("google", audio_bytes)
    return {"provider": "google", "path": str(path), "meta": data}


async def tts_azure(text: str, voice: str = "en-US-AriaNeural", **kwargs: Any) -> dict[str, Any]:
    endpoint = os.environ.get("AZURE_TTS_ENDPOINT")
    api_key = os.environ.get("AZURE_TTS_KEY")
    if not endpoint or not api_key:
        raise RuntimeError("AZURE_TTS_ENDPOINT 或 AZURE_TTS_KEY 未配置")
    ssml = kwargs.get("ssml")
    if not ssml:
        ssml = (
            f"<speak version='1.0' xml:lang='en-US'>"
            f"<voice name='{voice}'>{text}</voice>"
            "</speak>"
        )
    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": kwargs.get("format", "audio-16khz-128kbitrate-mono-mp3"),
    }
    resp = requests.post(endpoint, data=ssml.encode("utf-8"), headers=headers, timeout=30)
    resp.raise_for_status()
    path = _save_audio("azure", resp.content)
    return {"provider": "azure", "path": str(path)}


async def tts_index(text: str, voice: str = "default", **kwargs: Any) -> dict[str, Any]:
    endpoint = os.environ.get("INDEXTTS_ENDPOINT")
    if not endpoint:
        raise RuntimeError("INDEXTTS_ENDPOINT 未配置")
    payload = {"text": text, "voice": voice, **kwargs}
    resp = requests.post(endpoint, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    path = _handle_json_audio("indextts", data)
    return {"provider": "indextts", "path": str(path), "meta": data}


async def tts_gptsovits(text: str, speaker: str = "default", **kwargs: Any) -> dict[str, Any]:
    endpoint = os.environ.get("GPTSOVITS_ENDPOINT")
    if not endpoint:
        raise RuntimeError("GPTSOVITS_ENDPOINT 未配置")
    payload = {"text": text, "speaker": speaker, **kwargs}
    resp = requests.post(endpoint, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    path = _handle_json_audio("gptsovits", data)
    return {"provider": "gptsovits", "path": str(path), "meta": data}


async def tts_cosyvoice(text: str, voice: str = "default", **kwargs: Any) -> dict[str, Any]:
    endpoint = os.environ.get("COSYVOICE_ENDPOINT")
    if not endpoint:
        raise RuntimeError("COSYVOICE_ENDPOINT 未配置")
    payload = {"text": text, "voice": voice, **kwargs}
    resp = requests.post(endpoint, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    path = _handle_json_audio("cosyvoice", data)
    return {"provider": "cosyvoice", "path": str(path), "meta": data}
