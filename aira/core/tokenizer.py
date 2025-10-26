from __future__ import annotations

from typing import Iterable

import tiktoken


MODEL_TO_ENCODING = {
    # 常见 openai/vllm 兼容模型映射
    "gpt-4o": "o200k_base",
    "gpt-4o-mini": "o200k_base",
    "gpt-4.1": "o200k_base",
}


def count_tokens(text: str, model: str | None = None) -> int:
    enc_name = MODEL_TO_ENCODING.get(model or "", "cl100k_base")
    enc = tiktoken.get_encoding(enc_name)
    return len(enc.encode(text, disallowed_special=()))


def count_messages(messages: Iterable[str], model: str | None = None) -> int:
    return sum(count_tokens(m, model) for m in messages)


