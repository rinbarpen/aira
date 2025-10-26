from __future__ import annotations

from pathlib import Path
from typing import Any


def merge_lora(base_model_path: str, lora_path: str, output_path: str) -> str:
    try:
        from peft import PeftModel  # type: ignore
        from transformers import AutoModelForCausalLM
    except Exception as e:  # pragma: no cover - 需要安装 ml 额外依赖
        raise RuntimeError("peft/transformers not available; install [ml] extras") from e

    model = AutoModelForCausalLM.from_pretrained(base_model_path)
    merged = PeftModel.from_pretrained(model, lora_path)
    merged = merged.merge_and_unload()
    Path(output_path).mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(output_path, safe_serialization=True)
    return output_path


def quantize_gguf(model_path: str, output_path: str, qtype: str = "Q4_K_M") -> str:
    # 占位：实际可调用 llama.cpp 的 quantize，可在本地提供二进制或 Python 绑定
    # 这里仅演示返回路径。
    Path(output_path).mkdir(parents=True, exist_ok=True)
    return output_path


