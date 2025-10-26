# Chain-of-Thought 快速开始

## 一分钟上手

### 1. 启用 CoT 功能

编辑 `config/aira.toml`，确保包含以下配置：

```toml
[models.cot]
enabled = true              # 启用 CoT
show_reasoning = false      # 是否显示推理过程
enable_few_shot = true      # 使用少样本示例
models_to_wrap = [
    "qwen",      # 通义千问
    "kimi",      # Kimi
    "glm",       # 智谱GLM
    "deepseek",  # DeepSeek
    "ollama",    # Ollama
    "vllm",      # vLLM
    "hf",        # HuggingFace
]
```

### 2. 使用示例

#### CLI 使用

```bash
# 使用 Qwen（自动应用 CoT）
uv run python -m aira.server.cli chat --model qwen:qwen-plus

# 使用本地 Ollama 模型
uv run python -m aira.server.cli chat --model ollama:llama3
```

#### API 使用

```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "如何高效学习一门新的编程语言？",
    "session_id": "test",
    "model": "qwen:qwen-plus"
  }'
```

#### Python 代码

```python
import asyncio
from aira.models import build_gateway

async def main():
    gateway = build_gateway()
    
    # 使用包装了 CoT 的模型
    result = await gateway.generate(
        "qwen:qwen-plus",
        "解释递归算法的工作原理"
    )
    
    print(result.text)

asyncio.run(main())
```

### 3. 验证功能

运行快速测试（不需要 API 密钥）：

```bash
uv run python examples/quick_cot_test.py
```

运行完整示例（需要配置相应的 API 密钥）：

```bash
# 设置 API 密钥
export DASHSCOPE_API_KEY='your-key-here'

# 运行示例
uv run python examples/cot_example.py
```

## 效果对比

### 不使用 CoT

**提问**: 9.11 和 9.9 哪个更大？

**回答**: 9.11 更大。

（可能出错 ❌）

### 使用 CoT

**提问**: 9.11 和 9.9 哪个更大？

**回答**: 9.9 更大。9.9 = 9.90，而 9.11 = 9.11，所以 9.90 > 9.11。

（正确 ✅）

## 配置选项

### show_reasoning

控制是否显示推理过程：

```toml
show_reasoning = false  # 只显示答案（默认）
show_reasoning = true   # 显示推理过程 + 答案
```

**示例输出（show_reasoning = true）**:

```
【思考过程】
1. 比较两个小数需要对齐小数位
2. 9.11 = 9.11
3. 9.9 = 9.90
4. 90 > 11，所以 9.90 > 9.11

【最终答案】
9.9 更大
```

### enable_few_shot

控制是否使用少样本学习：

```toml
enable_few_shot = true   # 包含示例（推荐）
enable_few_shot = false  # 不包含示例（节省 token）
```

启用少样本会：
- ✅ 帮助模型更好理解格式
- ✅ 提高推理质量
- ❌ 增加约 200-300 个输入 token

### models_to_wrap

选择需要包装的模型：

```toml
# 只为 Qwen 启用
models_to_wrap = ["qwen"]

# 为多个模型启用
models_to_wrap = ["qwen", "kimi", "glm"]

# 禁用所有 CoT
models_to_wrap = []
# 或者
enabled = false
```

## 适用场景

### ✅ 适合使用 CoT

- 数学问题和逻辑推理
- 复杂的决策分析
- 需要多步骤推导的任务
- 代码调试和优化
- 需要权衡利弊的问题

### ❌ 不适合使用 CoT

- 简单的事实查询
- 闲聊对话
- 创意写作
- 快速响应需求（实时聊天）
- Token 预算紧张

## 成本估算

| 场景 | 不使用 CoT | 使用 CoT | 增加倍数 |
|------|-----------|----------|---------|
| 简单问答 | 150 tokens | 500 tokens | 3.3x |
| 复杂推理 | 300 tokens | 800 tokens | 2.7x |
| 长文本 | 1000 tokens | 2000 tokens | 2.0x |

💡 **建议**: 对于需要高质量推理的任务，CoT 带来的准确性提升通常值得额外的成本。

## 常见问题

### Q1: 模型不按格式输出怎么办？

A: CoT 包装器有回退机制，即使模型不遵循格式也能正常工作。建议：
1. 确保 `enable_few_shot = true`
2. 尝试不同的模型（Qwen 效果较好）

### Q2: 如何减少 token 消耗？

A: 可以：
1. 设置 `enable_few_shot = false`
2. 只在需要推理的任务上使用 CoT
3. 针对不同任务使用不同的模型配置

### Q3: OpenAI/Claude 需要启用 CoT 吗？

A: 不需要。这些模型支持原生推理能力，不应包装。配置中默认不包含这些模型。

### Q4: 本地模型（Ollama/vLLM）效果如何？

A: 取决于底层模型能力：
- Qwen2.5 7B/14B: 效果较好 ⭐⭐⭐⭐
- Llama 3 8B: 效果中等 ⭐⭐⭐
- Mistral 7B: 效果一般 ⭐⭐

## 下一步

- 📖 完整文档: [docs/cot_guide.md](cot_guide.md)
- 🧪 运行测试: `uv run python examples/quick_cot_test.py`
- 🎯 实际示例: `uv run python examples/cot_example.py`
- 🏗️ 架构说明: [docs/architecture.md](architecture.md)

## 技术支持

如有问题或建议，请：
1. 查看完整文档
2. 检查配置文件
3. 运行测试脚本验证
4. 提交 Issue 或 PR

