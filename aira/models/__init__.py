"""模型网关初始化。"""

from __future__ import annotations

from aira.core.config import get_app_config
from aira.models.adapters.openai_chat import OpenAIChatAdapter
from aira.models.adapters.openai_compatible import OpenAICompatibleAdapter
from aira.models.adapters.ollama import OllamaAdapter
from aira.models.adapters.vllm_openai import VllmOpenAIAdapter
from aira.models.adapters.hf_local import HFLocalAdapter
from aira.models.adapters.gemini import GeminiAdapter
from aira.models.adapters.anthropic import AnthropicAdapter
from aira.models.adapters.qwen import QwenAdapter
from aira.models.adapters.kimi import KimiAdapter
from aira.models.adapters.glm import GLMAdapter
from aira.models.adapters.deepseek import DeepSeekAdapter
from aira.models.gateway import ModelGateway, ModelAdapter
from aira.models.cot_wrapper import CoTWrapper


def build_gateway() -> ModelGateway:
    config = get_app_config()
    gateway = ModelGateway()

    enabled_models = [config["app"].get("default_model")]
    enabled_models.extend(config["models"].get("fallback", []))
    planner_model = config["models"].get("planner")
    if planner_model:
        enabled_models.append(planner_model)

    # 读取 CoT 配置
    cot_config = config.get("models", {}).get("cot", {})
    cot_enabled = cot_config.get("enabled", False)
    cot_show_reasoning = cot_config.get("show_reasoning", False)
    cot_enable_few_shot = cot_config.get("enable_few_shot", True)
    models_to_wrap = set(cot_config.get("models_to_wrap", []))

    def maybe_wrap_with_cot(adapter: ModelAdapter) -> ModelAdapter:
        """根据配置决定是否用 CoT 包装适配器。"""
        if cot_enabled and adapter.name in models_to_wrap:
            return CoTWrapper(
                adapter,
                show_reasoning=cot_show_reasoning,
                enable_few_shot=cot_enable_few_shot,
            )
        return adapter

    # OpenAI 官方API（支持原生 reasoning，不需要包装）
    gateway.register(OpenAIChatAdapter(), aliases=["openai:"])
    
    # OpenAI 兼容服务（通用适配器）
    compatible_adapter = maybe_wrap_with_cot(OpenAICompatibleAdapter())
    gateway.register(compatible_adapter, aliases=["openai_compatible:", "compatible:"])
    
    # vLLM OpenAI 兼容（保留向后兼容）
    vllm_adapter = maybe_wrap_with_cot(VllmOpenAIAdapter())
    gateway.register(vllm_adapter, aliases=["vllm:"])
    
    # Ollama
    ollama_adapter = maybe_wrap_with_cot(OllamaAdapter())
    gateway.register(ollama_adapter, aliases=["ollama:"])
    
    # HF 本地（Qwen/Llama + LoRA）
    hf_adapter = maybe_wrap_with_cot(HFLocalAdapter())
    gateway.register(hf_adapter, aliases=["hf:"])
    
    # Gemini (支持原生思维链，不需要包装)
    gateway.register(GeminiAdapter(), aliases=["gemini:"])
    
    # Claude (支持原生思维链，不需要包装)
    gateway.register(AnthropicAdapter(), aliases=["claude:"])
    
    # Qwen（Dashscope）
    qwen_adapter = maybe_wrap_with_cot(QwenAdapter())
    gateway.register(qwen_adapter, aliases=["qwen:"])
    
    # Kimi
    kimi_adapter = maybe_wrap_with_cot(KimiAdapter())
    gateway.register(kimi_adapter, aliases=["kimi:"])
    
    # GLM
    glm_adapter = maybe_wrap_with_cot(GLMAdapter())
    gateway.register(glm_adapter, aliases=["glm:"])
    
    # DeepSeek
    deepseek_adapter = maybe_wrap_with_cot(DeepSeekAdapter())
    gateway.register(deepseek_adapter, aliases=["deepseek:"])

    return gateway


def get_planner_model() -> str:
    config = get_app_config()
    return config.get("models", {}).get("planner", config["app"].get("default_model"))


__all__ = ["build_gateway", "get_planner_model"]

