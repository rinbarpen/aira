# aira

可学习的持久性高性能机器人！

## 快速概览
- 架构设计详见 `docs/architecture.md`
- 默认角色配置 `config/profiles/aira.toml`
- 全局配置 `config/aira.toml`
- `uv` 管理依赖与虚拟环境

## 功能规划
- 持续对话：短期缓存 + 长期向量记忆
- 多模态模型支持：Gemini、GPT、Claude、Qwen、Kimi、Deepseek、OpenRouter 等
- 工具与 MCP：统一工具协议，支持本地插件与 MCP Server
- 统计监控：token 消耗、推理时长、成本估算
- 角色管理：TOML 可配置，默认"可塑性记忆的艾拉"
- 接口形态：REST API + CLI + 桌面前端三种形态

## 项目结构
- `aira/core`：配置加载等基础组件
- `aira/dialogue`：对话编排器
- `aira/memory`：记忆服务
- `aira/models`：模型网关与适配器
- `aira/tools`：插件注册与工具调度
- `aira/stats`：统计与监控
- `aira/server/api`：FastAPI 服务入口
- `aira/server/cli`：Typer CLI 入口
- `aira/desktop`：PyQt6 桌面前端

## 开发说明
```bash
# 安装/同步依赖
uv sync

# 安装桌面前端依赖（可选）
uv sync --extra desktop

# 运行 CLI（入口为 main.py）
uv run python -m aira.server.cli --help

# 启动 API 服务
uv run uvicorn aira.server.api:create_app --factory --reload

# 启动 CLI 热加载配置示例
uv run python -m aira.server.cli chat --session demo

# 启动桌面前端（需要先启动 API 服务）
uv run python run_desktop.py

# 启动增强版桌面前端（推荐）
uv run python run_desktop_enhanced.py
```

## 桌面前端
AIRA 提供了两个版本的桌面应用：

### 基础版 (`run_desktop.py`)
- ✨ 美观的对话界面（气泡式消息显示）
- 🔄 多会话管理和角色切换
- 📊 实时连接状态监控
- ⚙️ 灵活的配置管理

### 增强版 (`run_desktop_enhanced.py`) - 推荐
在基础版功能之上，新增：
- 🌊 **流式响应**：实时显示 AI 生成内容
- 💾 **本地存储**：对话历史自动保存（SQLite）
- 🖼️ **图像支持**：上传和显示图片
- 🎤 **语音消息**：录音、播放、ASR 识别
- 📄 **文档上传**：支持多种文档格式
- 🎨 **自定义主题**：6种精美主题随心切换
- ⚡ **便捷回复**：快速回复常用短语
- 🌍 **多语言**：可限定 AI 回复语言

详细使用说明：
- 基础版：[README_DESKTOP.md](README_DESKTOP.md)
- 增强版：[README_DESKTOP_ENHANCED.md](README_DESKTOP_ENHANCED.md)
- 完整指南：[docs/desktop_guide.md](docs/desktop_guide.md)

## 特性速览
- **配置热加载**：`ConfigWatcher` 配合 watchfiles 实时刷新 TOML 配置
- **模型网关**：已接入 `openai`(Chat Completions 兼容)、`vllm`(OpenAI兼容)、`ollama`、`hf`(本地 Qwen/Llama)、`gemini`，可通过前缀/别名路由
- **外接思维链 (CoT)**：为不支持原生思维链的模型（Qwen、Kimi、GLM、DeepSeek等）提供外接 Chain-of-Thought 功能，通过提示工程引导逐步推理
- **工具执行**：`ToolRunner` 支持本地函数与 MCP Server 调用，配置驱动加载
- **统计追踪**：`StatsTracker` 记录 token、时长等指标，后续可持久化
- **媒体工具**：`capture_photo` 调用摄像头拍照，`screenshot` 抓取屏幕，均返回本地路径和 data-uri
- **创意贴纸**：`sticker_picker` 与 emoji 策略结合，支持回复表情包链接
- **预设人格**：内置 `aira`、`tsundere`、`cold`、`straight`、`dark`、`ojousama`、`king`、`slave`、`otaku`、`athlete` 等配置，可通过 `config/profiles/*.toml` 切换

## LLM 适配器使用
- 环境变量（按需设置）
  - OpenAI: `OPENAI_API_KEY`，可选 `OPENAI_BASE_URL`（代理或自建网关）
  - vLLM: `VLLM_BASE_URL`（默认 `http://localhost:8000/v1`），可选 `VLLM_API_KEY`
  - Ollama: `OLLAMA_BASE_URL`（默认 `http://localhost:11434`）
  - Gemini: `GEMINI_API_KEY`，可选 `GEMINI_MODEL`

- 请求模型名规则：`<前缀>:<模型名>`
  - `openai:gpt-4o`、`vllm:qwen2.5`、`ollama:llama3`

- 通过 API 指定模型（示例）：
```bash
curl -s http://localhost:8080/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"hello","session_id":"s1","persona_id":"aira"}'
```
（默认模型读取 `config/aira.toml` 的 `app.default_model`，亦可扩展接口在 body 中传入 `model` 字段）

## Chain-of-Thought (思维链) 功能

AIRA 为不支持原生思维链的模型提供了外接 CoT 功能，通过提示工程引导模型进行逐步推理。

### 适用模型

**推荐启用 CoT 的模型**（不支持原生思维链）：
- Qwen（通义千问）
- Kimi（月之暗面）
- GLM（智谱）
- DeepSeek（非 R1 版本）
- Ollama 本地模型
- vLLM 本地部署
- HuggingFace 本地模型

**不需要 CoT 的模型**（支持原生推理）：
- OpenAI o1/o1-mini
- Claude 3.5 Sonnet
- Gemini Pro
- DeepSeek R1

### 配置

在 `config/aira.toml` 中启用：

```toml
[models.cot]
enabled = true              # 启用 CoT 功能
show_reasoning = false      # 是否显示推理过程
enable_few_shot = true      # 使用少样本示例
models_to_wrap = [
    "qwen", "kimi", "glm", "deepseek",
    "ollama", "vllm", "hf"
]
```

### 使用示例

```bash
# CLI 使用（自动应用 CoT）
uv run python -m aira.server.cli chat --model qwen:qwen-plus

# 运行演示脚本
uv run python examples/cot_example.py
```

详细文档请查看 [docs/cot_guide.md](docs/cot_guide.md)