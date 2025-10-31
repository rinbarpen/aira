"""模型网关初始化。"""

from __future__ import annotations

from aira.core.config import get_app_config
from aira.models.adapters.openai_chat import OpenAIChatAdapter
from aira.models.adapters.ollama import OllamaAdapter
from aira.models.adapters.vllm_openai import VllmOpenAIAdapter
from aira.models.adapters.hf_local import HFLocalAdapter
from aira.models.adapters.gemini import GeminiAdapter
from aira.models.adapters.anthropic import AnthropicAdapter
from aira.models.adapters.qwen import QwenAdapter
from aira.models.adapters.kimi import KimiAdapter
from aira.models.adapters.glm import GLMAdapter
from aira.models.adapters.deepseek import DeepSeekAdapter
from aira.models.cot_embedding import CoTEmbeddingWrapper, CoTGeneratorOptions
from aira.models.cot_wrapper import CoTWrapper
from aira.models.gateway import ModelGateway, ModelAdapter


def _normalize_provider_name(model_name: str) -> str:
    if not model_name:
        return ""
    return model_name.split(":", 1)[0]


def build_gateway() -> ModelGateway:
    config = get_app_config()
    gateway = ModelGateway()

    models_config = config.get("models", {})

    cot_config = models_config.get("cot", {})
    cot_enabled = cot_config.get("enabled", False)
    cot_show_reasoning = cot_config.get("show_reasoning", False)
    cot_enable_few_shot = cot_config.get("enable_few_shot", True)
    cot_models_to_wrap = set(cot_config.get("models_to_wrap", []))

    cot_embedding_config = models_config.get("cot_embedding", {})
    cot_embedding_enabled = cot_embedding_config.get("enabled", False)
    cot_embedding_targets = {
        _normalize_provider_name(name) for name in cot_embedding_config.get("models_to_wrap", [])
    }
    cot_embedding_generator = cot_embedding_config.get("generator", "deepseek")
    generator_provider = _normalize_provider_name(cot_embedding_generator)
    generator_options_kwargs = {}
    if cot_embedding_config.get("generator_model"):
        generator_options_kwargs["model"] = cot_embedding_config.get("generator_model")
    if cot_embedding_config.get("generator_max_tokens") is not None:
        generator_options_kwargs["max_tokens"] = cot_embedding_config.get("generator_max_tokens")
    if cot_embedding_config.get("generator_temperature") is not None:
        generator_options_kwargs["temperature"] = cot_embedding_config.get("generator_temperature")
    cot_generator_options = (
        CoTGeneratorOptions(**generator_options_kwargs) if generator_options_kwargs else None
    )
    cot_embedding_show_reasoning = cot_embedding_config.get("show_reasoning", False)
    cot_prompt_template = cot_embedding_config.get("cot_prompt_template")
    cot_system_prompt_template = cot_embedding_config.get("system_prompt_template")

    raw_adapters: dict[str, ModelAdapter] = {
        "openai": OpenAIChatAdapter(),
        "vllm": VllmOpenAIAdapter(),
        "ollama": OllamaAdapter(),
        "hf": HFLocalAdapter(),
        "gemini": GeminiAdapter(),
        "claude": AnthropicAdapter(),
        "qwen": QwenAdapter(),
        "kimi": KimiAdapter(),
        "glm": GLMAdapter(),
        "deepseek": DeepSeekAdapter(),
    }

    alias_map: dict[str, list[str]] = {
        "openai": ["openai:"],
        "vllm": ["vllm:"],
        "ollama": ["ollama:"],
        "hf": ["hf:"],
        "gemini": ["gemini:"],
        "claude": ["claude:"],
        "qwen": ["qwen:"],
        "kimi": ["kimi:"],
        "glm": ["glm:"],
        "deepseek": ["deepseek:"],
    }

    adapters: dict[str, ModelAdapter] = {}

    for name, adapter in raw_adapters.items():
        if cot_enabled and name in cot_models_to_wrap:
            adapter = CoTWrapper(
                adapter,
                show_reasoning=cot_show_reasoning,
                enable_few_shot=cot_enable_few_shot,
            )
        adapters[name] = adapter

    generator_adapter = raw_adapters.get(generator_provider) if cot_embedding_enabled else None
    if cot_embedding_enabled and generator_adapter is None:
        raise KeyError(f"未找到用于 CoT 嵌入的生成适配器: {cot_embedding_generator}")

    if cot_embedding_enabled:
        for name, adapter in list(adapters.items()):
            if name not in cot_embedding_targets:
                continue
            adapters[name] = CoTEmbeddingWrapper(
                adapter,
                generator_adapter,
                generator_options=cot_generator_options,
                cot_prompt_template=cot_prompt_template,
                system_prompt_template=cot_system_prompt_template,
                show_reasoning=cot_embedding_show_reasoning,
            )

    for name, adapter in adapters.items():
        gateway.register(adapter, aliases=alias_map.get(name, []))

    return gateway


def get_planner_model() -> str:
    config = get_app_config()
    return config.get("models", {}).get("planner", config["app"].get("default_model"))


__all__ = ["build_gateway", "get_planner_model"]

