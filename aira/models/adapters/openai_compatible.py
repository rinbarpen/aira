"""OpenAI兼容服务适配器

支持任何实现OpenAI /v1/chat/completions协议的服务，如：
- vLLM
- LocalAI
- Ollama (OpenAI模式)
- Text-generation-webui
- 其他自定义服务
"""

from __future__ import annotations

import os
from typing import Any

from aira.models.gateway import ModelAdapter, SimpleCompletionResult
from aira.core.http import post_json
from aira.core.tokenizer import count_tokens


class OpenAICompatibleAdapter(ModelAdapter):
    """OpenAI兼容服务适配器（非官方OpenAI）"""
    
    name = "openai_compatible"

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        """初始化OpenAI兼容适配器
        
        Args:
            base_url: 服务端点URL（默认从环境变量读取）
            api_key: API密钥（默认从环境变量读取，可选）
        """
        self._base_url = base_url or os.environ.get(
            "OPENAI_COMPATIBLE_BASE_URL",
            "http://localhost:8000/v1"  # 默认本地vLLM端点
        )
        self._api_key = api_key or os.environ.get("OPENAI_COMPATIBLE_API_KEY", "")

    async def generate(self, prompt: str, **kwargs: Any) -> SimpleCompletionResult:
        """生成文本
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
                - model: 模型名称（默认从环境变量或配置读取）
                - messages: 消息列表（如果提供，忽略prompt）
                - temperature: 温度
                - max_tokens: 最大token数
                
        Returns:
            生成结果
        """
        # 获取模型名称
        model = kwargs.get("model", os.environ.get("OPENAI_COMPATIBLE_MODEL", "default"))
        
        # 构建消息
        messages = kwargs.get("messages") or [
            {"role": "user", "content": prompt},
        ]
        
        # 构建请求体
        body = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 512),
            "stream": False,
        }
        
        # 构建请求头
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        
        # 调用API
        data = await post_json(
            f"{self._base_url}/chat/completions",
            headers=headers,
            json=body,
            timeout=60
        )
        
        # 解析响应
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        
        # 如果没有usage信息，估算token数
        if not usage:
            usage = {
                "input_tokens": count_tokens("\n".join(m["content"] for m in messages), model),
                "output_tokens": count_tokens(text, model),
            }
        
        return SimpleCompletionResult(text=text, usage=usage)

    async def count_tokens(self, text: str) -> int:
        """计算token数量
        
        Args:
            text: 文本
            
        Returns:
            token数量
        """
        return count_tokens(text)

