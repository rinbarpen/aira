# Chain-of-Thought (思维链) 外接功能指南

## 概述

AIRA 提供了外接的 Chain-of-Thought (CoT) 功能，可以为不支持原生思维链的模型提供逐步推理能力。通过提示工程和结构化输出，引导模型进行深入思考后再给出最终答案。

## 适用场景

### 适合使用 CoT 的模型

以下模型**不支持原生思维链**，建议启用 CoT 包装器：

- **Qwen (通义千问)**: `qwen:qwen-plus`, `qwen:qwen-turbo`
- **Kimi (月之暗面)**: `kimi:moonshot-v1`
- **GLM (智谱)**: `glm:glm-4`, `glm:glm-4v`
- **DeepSeek (非R1版本)**: `deepseek:deepseek-chat`
- **Ollama 本地模型**: `ollama:llama3`, `ollama:mistral`
- **vLLM 本地部署**: `vllm:qwen2.5`, `vllm:llama3`
- **HuggingFace 本地模型**: `hf:Qwen/Qwen2.5-7B-Instruct`

### 不需要 CoT 的模型

以下模型**支持原生思维链**，不需要额外包装：

- **OpenAI o1/o1-mini**: 内置推理能力
- **Claude 3.5 Sonnet**: Constitutional AI 推理
- **Gemini Pro**: 原生支持 CoT
- **DeepSeek R1**: 专门的推理模型

## 配置说明

### 基础配置

在 `config/aira.toml` 中配置 CoT 功能：

```toml
[models.cot]
enabled = true              # 启用 CoT 包装器
show_reasoning = false      # 是否在回复中显示推理过程
enable_few_shot = true      # 是否使用少样本示例

# 需要启用 CoT 的模型列表
models_to_wrap = [
    "qwen",
    "kimi",
    "glm",
    "deepseek",
    "ollama",
    "vllm",
    "hf",
]
```

### 配置参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | bool | true | 是否启用 CoT 功能 |
| `show_reasoning` | bool | false | 是否在最终回复中显示推理过程 |
| `enable_few_shot` | bool | true | 是否包含少样本示例帮助模型理解格式 |
| `models_to_wrap` | list | [] | 需要包装的模型名称列表 |

## 工作原理

### 1. 提示注入

CoT 包装器会自动向模型注入结构化的提示，要求其按照以下格式输出：

```
<思考>
1. 理解问题的核心
2. 分解问题要素
3. 逐步推导解决方案
4. 评估方案优劣
5. 得出结论
</思考>

<回答>
最终的简洁答案
</回答>
```

### 2. 少样本学习

启用 `enable_few_shot` 时，会提供示例帮助模型理解格式：

**示例 1: 数学比较**
- 问题：9.11 和 9.9 哪个更大？
- 展示完整的推理过程

**示例 2: 技术问题**
- 问题：如何提高 Python 代码执行效率？
- 展示结构化的分析方法

### 3. 响应解析

包装器会自动提取：
- **推理过程**: `<思考>` 标签内容
- **最终答案**: `<回答>` 标签内容

根据 `show_reasoning` 配置，决定是否在最终回复中包含推理过程。

## 使用示例

### CLI 使用

```bash
# 使用包装了 CoT 的 Qwen 模型
uv run python -m aira.server.cli chat --model qwen:qwen-plus

# 使用包装了 CoT 的本地 Ollama 模型
uv run python -m aira.server.cli chat --model ollama:llama3
```

### API 使用

```bash
# 发送请求到 Qwen (自动应用 CoT)
curl -s http://localhost:8080/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "解释量子纠缠的原理",
    "session_id": "test",
    "model": "qwen:qwen-plus"
  }'
```

### Python 编程使用

```python
from aira.models import build_gateway

# 构建网关（自动包装配置的模型）
gateway = build_gateway()

# 使用 Qwen（已包装 CoT）
result = await gateway.generate(
    "qwen:qwen-plus",
    "解释递归算法的优缺点"
)

print(result.text)
```

### 手动包装适配器

```python
from aira.models.adapters.qwen import QwenAdapter
from aira.models.cot_wrapper import wrap_adapter_with_cot

# 创建原始适配器
qwen = QwenAdapter()

# 手动包装为 CoT 版本
qwen_cot = wrap_adapter_with_cot(
    qwen,
    show_reasoning=True,  # 显示推理过程
    enable_few_shot=True
)

# 使用包装后的适配器
result = await qwen_cot.generate("什么是机器学习？")
```

## 高级配置

### 显示推理过程

当 `show_reasoning = true` 时，用户会看到完整的思考过程：

```
【思考过程】
1. 机器学习是人工智能的一个分支
2. 核心是让计算机从数据中学习规律
3. 主要分为监督学习、无监督学习和强化学习
4. 应用广泛，包括图像识别、自然语言处理等

【最终答案】
机器学习是一种让计算机通过数据学习并改进性能的技术，
无需显式编程，广泛应用于各种 AI 任务。
```

### 隐藏推理过程

当 `show_reasoning = false` 时（默认），只显示最终答案：

```
机器学习是一种让计算机通过数据学习并改进性能的技术，
无需显式编程，广泛应用于各种 AI 任务。
```

### 自定义包装的模型

修改 `models_to_wrap` 列表来控制哪些模型需要 CoT：

```toml
# 只为 Qwen 和 Ollama 启用 CoT
models_to_wrap = ["qwen", "ollama"]

# 为所有支持的模型启用 CoT
models_to_wrap = ["qwen", "kimi", "glm", "deepseek", "ollama", "vllm", "hf"]

# 禁用所有 CoT（空列表或设置 enabled = false）
models_to_wrap = []
```

## 性能考虑

### Token 消耗

- CoT 会增加输入 token（提示模板 + 少样本示例）
- 输出 token 也会增加（推理过程 + 答案）
- 包装器会自动将 `max_tokens` 增加 1.5 倍

### 推理时间

- CoT 需要模型生成更多内容，会增加响应时间
- 对于复杂问题，推理质量的提升通常值得额外的时间开销

### 成本估算

```python
# 示例：不使用 CoT
输入: 100 tokens
输出: 50 tokens
总计: 150 tokens

# 使用 CoT
输入: 300 tokens (系统提示 + 少样本 + 用户问题)
输出: 200 tokens (推理 + 答案)
总计: 500 tokens (~3.3x)
```

## 最佳实践

### 1. 何时使用 CoT

✅ **适合使用**:
- 复杂的逻辑推理问题
- 需要多步骤分析的任务
- 数学计算和证明
- 代码调试和优化建议
- 需要权衡利弊的决策

❌ **不建议使用**:
- 简单的事实查询
- 闲聊对话
- 快速响应场景
- Token 预算有限的情况

### 2. 调试技巧

启用 `show_reasoning = true` 来调试：

```toml
[models.cot]
enabled = true
show_reasoning = true  # 临时启用以查看推理过程
enable_few_shot = true
```

### 3. 模型选择建议

不同模型对 CoT 的响应效果：

| 模型 | CoT 效果 | 推荐场景 |
|------|----------|----------|
| Qwen-Plus | ⭐⭐⭐⭐⭐ | 通用推理，成本适中 |
| Qwen-Turbo | ⭐⭐⭐⭐ | 快速响应，成本低 |
| Kimi | ⭐⭐⭐⭐ | 长文本分析 |
| GLM-4 | ⭐⭐⭐⭐ | 中文推理 |
| DeepSeek-Chat | ⭐⭐⭐ | 代码相关推理 |
| Ollama 本地 | ⭐⭐⭐ | 隐私敏感，无成本 |

## 故障排除

### 模型不按格式输出

如果模型不遵循 `<思考>` 和 `<回答>` 标签：

1. 确保 `enable_few_shot = true`，示例有助于模型理解格式
2. 尝试不同的模型，某些模型指令遵循能力更强
3. 包装器有回退机制，即使格式不正确也能正常返回

### CoT 未生效

检查配置：

```bash
# 查看配置是否正确加载
grep -A 10 "models.cot" config/aira.toml

# 确认模型名称在 models_to_wrap 列表中
```

### Token 超限

如果遇到 token 限制：

```toml
[models.cot]
enable_few_shot = false  # 禁用少样本以减少 token
```

或者调整请求参数：

```python
result = await gateway.generate(
    "qwen:qwen-plus",
    prompt,
    max_tokens=4096  # 增加限制
)
```

## 扩展开发

### 自定义 CoT 提示

如果需要自定义提示模板，可以扩展 `CoTWrapper`：

```python
from aira.models.cot_wrapper import CoTWrapper

class CustomCoTWrapper(CoTWrapper):
    COT_SYSTEM_PROMPT = """你的自定义提示..."""
    
    COT_USER_TEMPLATE = """你的自定义模板...
    
    {original_prompt}
    """
```

### 添加新的模型支持

1. 在 `aira/models/adapters/` 中实现适配器
2. 在 `aira/models/__init__.py` 中注册
3. 在 `config/aira.toml` 的 `models_to_wrap` 中添加模型名

## 参考资料

- [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903)
- [Large Language Models are Zero-Shot Reasoners](https://arxiv.org/abs/2205.11916)
- AIRA 架构文档: `docs/architecture.md`

## 更新日志

### v1.0.0 (2025-01-01)
- ✨ 初始实现 CoT 包装器
- ✨ 支持配置驱动的模型包装
- ✨ 少样本学习示例
- ✨ 推理过程显示/隐藏控制
- 📝 完整的使用文档和示例

