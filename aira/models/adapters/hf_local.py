"""HuggingFace 本地适配器，支持 Qwen/Llama 与 LoRA 权重加载。"""

from __future__ import annotations

import os
from typing import Any

from aira.core.config import get_app_config
from aira.core.tokenizer import count_tokens
from aira.models.gateway import ModelAdapter, SimpleCompletionResult


class HFLocalAdapter(ModelAdapter):
    name = "hf"

    def __init__(self) -> None:
        self._cache: dict[tuple[str, str | None, bool, bool, str], tuple[Any, Any]] = {}
        self._kv_cache: dict[tuple[str, str | None, str], dict[str, Any]] = {}
        hardware_cfg = get_app_config().get("hardware", {})
        self._default_device_map = hardware_cfg.get("hf_device_map", "cpu")

    def _lazy_imports(self):  # type: ignore
        try:
            import torch  # noqa: F401
        except ImportError as exc:  # pragma: no cover - 环境缺失 torch
            raise RuntimeError("运行本地 HF 模型需要安装 PyTorch") from exc
        global AutoTokenizer, AutoModelForCausalLM, PeftModel  # noqa: N816
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
        try:
            from peft import PeftModel  # type: ignore
        except Exception:  # pragma: no cover - 可选
            PeftModel = None  # type: ignore

    def _load_model(
        self,
        model_id: str,
        lora_path: str | None,
        load_8bit: bool,
        load_4bit: bool,
        device_map: str,
    ) -> tuple[Any, Any]:
        if load_4bit and load_8bit:
            raise ValueError("load_in_4bit 与 load_in_8bit 不能同时为 True")
        self._lazy_imports()
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

        quant_kwargs: dict[str, Any] = {}
        if load_4bit:
            quant_kwargs["load_in_4bit"] = True
        elif load_8bit:
            quant_kwargs["load_in_8bit"] = True

        tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map=device_map,
            trust_remote_code=True,
            **quant_kwargs,
        )
        if lora_path:
            try:
                from peft import PeftModel  # type: ignore

                model = PeftModel.from_pretrained(model, lora_path)
            except Exception as exc:  # pragma: no cover - LoRA 加载失败
                raise RuntimeError(f"加载 LoRA 权重失败: {lora_path}") from exc
        model.eval()
        return tokenizer, model

    def _get_bundle(
        self,
        model_id: str,
        lora_path: str | None,
        load_8bit: bool,
        load_4bit: bool,
        device_map: str | None,
    ) -> tuple[Any, Any]:
        map_value = device_map or self._default_device_map
        key = (model_id, lora_path, load_8bit, load_4bit, map_value)
        if key not in self._cache:
            self._cache[key] = self._load_model(model_id, lora_path, load_8bit, load_4bit, map_value)
        return self._cache[key]

    def _build_prompt(self, tokenizer: Any, prompt: str, messages: list[dict[str, Any]] | None) -> str:
        if messages:
            # 尝试使用模型提供的 chat template
            if hasattr(tokenizer, "apply_chat_template"):
                try:
                    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                except Exception:  # pragma: no cover - 模板失败则回退
                    pass
            parts = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                parts.append(f"{role.upper()}: {content}")
            parts.append("ASSISTANT:")
            return "\n".join(parts)
        return prompt

    async def generate(self, prompt: str, **kwargs: Any) -> SimpleCompletionResult:
        model_id = kwargs.get("model") or os.environ.get("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        lora_path = kwargs.get("lora_path") or os.environ.get("HF_LORA_PATH")
        device_map = kwargs.get("device_map")
        load_8bit = bool(kwargs.get("load_in_8bit", False))
        load_4bit = bool(kwargs.get("load_in_4bit", False))
        max_new_tokens = int(kwargs.get("max_tokens", 512))
        temperature = float(kwargs.get("temperature", 0.7))
        messages = kwargs.get("messages")
        session_id = kwargs.get("session_id", "default")
        use_cache = bool(kwargs.get("use_cache", True))

        tokenizer, model = self._get_bundle(model_id, lora_path, load_8bit, load_4bit, device_map)
        prompt_text = self._build_prompt(tokenizer, prompt, messages)

        try:
            import torch
        except ImportError as exc:  # pragma: no cover - 环境缺失 torch
            raise RuntimeError("运行本地 HF 模型需要安装 PyTorch") from exc

        inputs = tokenizer(prompt_text, return_tensors="pt").to(model.device)
        prompt_ids = inputs["input_ids"]

        cache_key = (model_id, lora_path, session_id)
        cache_entry = self._kv_cache.get(cache_key) if use_cache else None

        generate_kwargs = {
            "do_sample": True,
            "temperature": temperature,
            "max_new_tokens": max_new_tokens,
            "return_dict_in_generate": True,
            "use_cache": True,
        }

        if cache_entry:
            prev_ids = cache_entry["prompt_ids"]
            past = cache_entry["past"]
            prev_tensor = cache_entry["prompt_tensor"]
            if prompt_ids.shape[1] >= prev_tensor.shape[1]:
                current_ids_list = prompt_ids[0].tolist()
                prev_list = prev_ids
                if current_ids_list[: len(prev_list)] == prev_list:
                    delta_len = len(current_ids_list) - len(prev_list)
                    new_prompt_tensor = None
                    if delta_len > 0:
                        new_prompt_tensor = prompt_ids[:, -delta_len:]
                    with torch.no_grad():
                        outputs = model.generate(
                            input_ids=new_prompt_tensor,
                            past_key_values=past,
                            **generate_kwargs,
                        )
                    sequences = outputs.sequences
                    generated = sequences[:, new_prompt_tensor.shape[1] if new_prompt_tensor is not None else 0 :]
                    full_sequence = torch.cat([prev_tensor, new_prompt_tensor if new_prompt_tensor is not None else torch.empty((1,0), dtype=prev_tensor.dtype, device=model.device), generated], dim=1)
                    text = tokenizer.decode(full_sequence[0], skip_special_tokens=True)
                    self._kv_cache[cache_key] = {
                        "prompt_ids": current_ids_list,
                        "prompt_tensor": torch.cat([prev_tensor, new_prompt_tensor], dim=1) if new_prompt_tensor is not None else prev_tensor,
                        "past": outputs.past_key_values,
                    }
                    usage = {
                        "input_tokens": count_tokens(prompt_text, model_id),
                        "output_tokens": count_tokens(text, model_id),
                    }
                    return SimpleCompletionResult(text=text[len(prompt_text) :].strip() or text, usage=usage)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                **generate_kwargs,
            )
        sequences = outputs.sequences
        generated_ids = sequences[0, prompt_ids.shape[1] :]
        text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        self._kv_cache[cache_key] = {
            "prompt_ids": prompt_ids[0].tolist(),
            "prompt_tensor": prompt_ids.detach(),
            "past": outputs.past_key_values,
        }
        usage = {
            "input_tokens": count_tokens(prompt_text, model_id),
            "output_tokens": count_tokens(text, model_id),
        }
        return SimpleCompletionResult(text=text, usage=usage)

    async def count_tokens(self, text: str) -> int:
        return count_tokens(text)


