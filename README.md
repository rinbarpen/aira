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

## ✨ 高级功能

Aira现已支持四大高级功能，让AI助手更加智能和生动：

### 🧠 长期人格进化
- **根据交互历史动态调整性格**：温暖度、幽默感、共情力等7种特征自动进化
- **用户偏好学习**：统计反馈、情感、话题，让AI越来越懂你
- **状态持久化**：进化数据自动保存，重启不丢失

### 👁️ 视觉认知
- **表情识别**：通过摄像头识别用户的9种情绪状态
- **姿态检测**：检测用户坐姿，评估参与度和疲劳度
- **智能响应**：根据用户状态自动调整回复策略
- 依赖：OpenCV + MediaPipe

### 🎭 3D Avatar控制
- **多平台支持**：Unity3D、VRoid、Live2D
- **情绪驱动表达**：根据对话内容自动控制Avatar表情和动作
- **实时口型同步**：支持语音驱动的口型动画
- **眼球追踪**：Avatar可以看向用户或其他目标

### 👥 多Agent社交
- **多AI对话**：不同人格的AI之间可以互相对话
- **社交场景**：支持辩论、闲聊、教学、角色扮演等场景
- **关系追踪**：记录Agent之间的关系变化
- **对话记录**：完整保存多Agent交互历史

详细文档：
- 📖 [高级功能使用指南](docs/advanced_features_guide.md)
- 📝 [功能实现总结](ADVANCED_FEATURES.md)
- 🎮 [示例代码](examples/advanced_features_demo.py)

## 项目结构
- `aira/core`：配置加载等基础组件
- `aira/dialogue`：对话编排器
- `aira/memory`：记忆服务
- `aira/models`：模型网关与适配器
- `aira/translation`：智能翻译Agent
- `aira/tts`：TTS语音合成模块
- `aira/asr`：ASR语音识别模块
- `aira/tools`：插件注册与工具调度
- `aira/stats`：统计与监控
- `aira/monitor`：独立监控Web服务
- `aira/server/api`：FastAPI 服务入口
- `aira/server/cli`：Typer CLI 入口
- `aira/desktop`：PyQt6 桌面前端

## 快速开始

### 1. 安装依赖
```bash
# 基础安装
uv sync

# 安装所有高级功能（推荐）
uv pip install -e ".[full]"
```

### 2. 配置模型（三选一）

**选项 A: OpenAI（国际用户）**
```bash
# 创建 .env 文件
echo "OPENAI_API_KEY=sk-your-key" > .env

# 编辑 config/aira.toml
default_model = "openai:gpt-4o-mini"
```

> 💡 **支持 OpenAI 兼容服务**：可通过 `OPENAI_BASE_URL` 使用任何兼容 API（国内中转、DeepSeek、Azure 等）  
> 详见 [OPENAI_COMPATIBLE_README.md](OPENAI_COMPATIBLE_README.md)

**选项 B: DeepSeek（国内推荐）**
```bash
echo "DEEPSEEK_API_KEY=your-key" > .env
# config/aira.toml
default_model = "deepseek:deepseek-chat"
```

**选项 C: Ollama（本地免费）**
```bash
# 安装 Ollama: https://ollama.com
ollama pull llama3

# config/aira.toml
default_model = "ollama:llama3"
```

**详细配置**: 参阅 [OPENAI_SETUP_GUIDE.md](OPENAI_SETUP_GUIDE.md)

### 3. 运行
```bash
# 测试
uv run python examples/quick_test_advanced.py

# 启动对话
uv run python -m aira.server.cli chat
```

## 开发说明
```bash
# 安装桌面前端依赖（可选）
uv sync --extra desktop

# 分模块安装高级功能（可选）
uv pip install -e ".[vision]"    # 视觉认知
uv pip install -e ".[avatar]"    # Avatar控制
uv pip install -e ".[social]"    # 多Agent社交

# 运行 CLI（入口为 main.py）
uv run python -m aira.server.cli --help

# 启动 API 服务
uv run uvicorn aira.server.api:create_app --factory --reload

# 启动 CLI 交互对话（支持流式输出、角色切换、角色扮演）
uv run python -m aira.server.cli chat --session demo

# 指定初始角色
uv run python -m aira.server.cli chat --persona tsundere

# 关闭流式输出
uv run python -m aira.server.cli chat --session demo --no-stream

# 对话中可用命令：
# /switch <角色> - 切换预设角色（支持16+种预设角色）
#   基础: aira, tsundere, cold, straight, dark, ojousama, king, slave, otaku, athlete
#   经典角色: charas/aira_plastic_memories, charas/atri, charas/kohaku, charas/renge, charas/kurisu, charas/youmu
# /role <角色> - 角色扮演模式（自由扮演任意角色）
# /reset - 重置角色
# /help - 帮助

# 启动桌面前端（需要先启动 API 服务）
uv run python run_desktop.py

# 或通过 CLI 启动
uv run python -m aira.server.cli desktop
```

## 桌面前端
AIRA 提供了功能完整的增强版桌面应用：

### 增强版桌面应用 (`run_desktop.py`)
- 🌊 **流式响应**：实时显示 AI 生成内容
- 💾 **本地存储**：对话历史自动保存（SQLite）
- 🖼️ **图像支持**：上传和显示图片
- 🎤 **语音消息**：录音、播放、ASR 识别
- 📄 **文档上传**：支持多种文档格式
- 🎨 **自定义主题**：6种精美主题随心切换
- ⚡ **便捷回复**：快速回复常用短语
- 🌍 **多语言**：可限定 AI 回复语言
- ✨ **美观界面**：气泡式消息显示
- 🔄 **多会话管理**：会话和角色切换
- 📊 **状态监控**：实时连接状态显示

详细使用说明：
- [README_DESKTOP_ENHANCED.md](README_DESKTOP_ENHANCED.md)
- [docs/desktop_guide.md](docs/desktop_guide.md)

## 📊 Monitor 监控服务

Aira提供独立的Web监控服务，实时查看AI使用情况。**Monitor作为独立进程运行，即使主程序关闭也能继续访问。**

### 特性
- ✅ **独立进程**：与主程序分离，互不影响
- 📈 **实时统计**：请求数、Token使用量、成本分析
- 🌐 **Web界面**：美观的可视化仪表板
- 🔌 **REST API**：完整的API接口
- 🔄 **自动刷新**：每30秒自动更新数据
- 📊 **多维度分析**：按模型、会话、时间统计

### 快速启动

**Windows**:
```powershell
# 后台运行
.\start_monitor.ps1

# 访问Web界面
# http://localhost:8090
```

**Linux/macOS**:
```bash
# 给脚本添加执行权限（首次运行）
chmod +x start_monitor.sh stop_monitor.sh

# 后台运行
./start_monitor.sh

# 访问Web界面
# http://localhost:8090
```

### 管理命令

```bash
# 停止服务
./stop_monitor.sh       # Linux/macOS
.\stop_monitor.ps1      # Windows

# 重启服务
./restart_monitor.sh    # Linux/macOS
.\restart_monitor.ps1   # Windows

# 查看日志
tail -f logs/monitor.log              # Linux/macOS
Get-Content logs\monitor.log -Wait    # Windows
```

### API接口

```bash
# 获取统计摘要
curl http://localhost:8090/api/stats/summary?days=7

# 获取最近请求
curl http://localhost:8090/api/stats/recent?limit=50

# 健康检查
curl http://localhost:8090/api/health
```

详细文档：[docs/monitor_guide.md](docs/monitor_guide.md)

## 🎤 TTS (Text-to-Speech) 语音合成 + 智能翻译

Aira集成了强大的TTS功能和智能翻译Agent，让AI助手能够"说话"并支持多语言输出！

### 支持的TTS服务

| 提供商 | 成本 | 质量 | 特点 |
|--------|------|------|------|
| **Edge TTS** | 免费 | 高 | 推荐日常使用，无需API密钥 |
| **Minimax** | 付费 | 极高 | 中文质量最佳 |
| **Azure TTS** | 付费 | 极高 | 企业级，支持100+语言 |
| **Google Cloud TTS** | 付费 | 极高 | WaveNet，最自然 |

### 快速使用

```python
from aira.tts import get_tts_gateway

# 使用免费的Edge TTS
gateway = get_tts_gateway()

# 方式1: 自动检测语言并选择合适的语音（推荐）
result = await gateway.synthesize(
    text="你好，我是艾拉！",  # 自动检测中文，选择中文语音
    provider="edge",
    auto_detect_language=True  # 默认开启
)

# 方式2: 指定偏好语言
result = await gateway.synthesize(
    text="Hello! 你好！",  # 混合语言
    provider="edge",
    preferred_language="en"  # 强制使用英文语音
)

# 方式3: 完全手动指定
result = await gateway.synthesize(
    text="你好，我是艾拉！",
    provider="edge",
    voice="zh-CN-XiaoxiaoNeural"  # 手动指定
)

print(f"音频文件: {result.audio_path}")
```

### 🌐 智能翻译 + TTS（新功能！）

**场景**：LLM用中文回复，但希望TTS输出日语/英语等其他语言

```python
from aira.tts import get_tts_gateway

gateway = get_tts_gateway()

# LLM用中文思考和回复（成本低）
llm_output_zh = "你好，今天天气真好！"

# 自动翻译为日语并生成日语语音
result = await gateway.synthesize(
    text=llm_output_zh,
    provider="edge",
    auto_translate=True,    # 启用自动翻译
    target_language="ja"    # 目标语言：日语
)

print(f"音频文件: {result.audio_path}")
# 输出: 日语语音文件（内容已自动翻译）
```

**成本优势**：
- LLM: 使用便宜的中文模型
- 翻译: 使用gpt-4o-mini（$0.15/1M tokens）
- TTS: 使用免费的Edge TTS
- **总成本：极低！**

### 测试TTS

```bash
# 测试所有提供商
python examples/test_tts.py

# 测试特定提供商
python examples/test_tts.py --provider edge

# 列出所有可用语音
python examples/test_tts.py --list-voices
```

### 环境变量配置

```bash
# .env 文件（可选）
MINIMAX_API_KEY=your_minimax_api_key       # Minimax
AZURE_TTS_KEY=your_azure_key               # Azure
GOOGLE_CLOUD_API_KEY=your_google_api_key   # Google
```

详细文档：[docs/tts_guide.md](docs/tts_guide.md)

## 🎙️ ASR (Automatic Speech Recognition) 语音识别

Aira集成了ASR功能，将语音转为文字，与TTS形成完整的语音对话能力！

### 支持的ASR服务

| 提供商 | 成本 | 质量 | 特点 |
|--------|------|------|------|
| **Faster-Whisper** | 免费 | 高 | 本地运行，推荐日常使用 |
| **OpenAI Whisper** | 付费 | 极高 | 官方API，97+语言 |
| **Azure Speech** | 付费 | 极高 | 企业级，实时识别 |
| **Google Speech** | 付费 | 极高 | 准确度最高 |

### 快速使用

```python
from aira.asr import get_asr_gateway

# 使用本地免费的Faster-Whisper
gateway = get_asr_gateway()
result = await gateway.transcribe(
    audio_path="audio.mp3",
    provider="faster_whisper"
)

print(f"识别结果: {result.text}")
print(f"检测语言: {result.language}")
```

### 完整语音对话

```python
from aira.tts import get_tts_gateway
from aira.asr import get_asr_gateway

# AI说话
tts = get_tts_gateway()
await tts.synthesize(text="你好！", provider="edge")

# 识别用户语音
asr = get_asr_gateway()
result = await asr.transcribe("user.mp3", provider="faster_whisper")
print(f"用户说: {result.text}")
```

### 测试ASR

```bash
# 测试ASR功能
python examples/test_asr.py

# 测试指定音频
python examples/test_asr.py --audio your_audio.mp3
```

### 环境变量配置（可选）

```bash
# .env 文件（云端API需要）
OPENAI_API_KEY=your_key                # OpenAI Whisper
AZURE_SPEECH_KEY=your_key              # Azure Speech  
GOOGLE_CLOUD_API_KEY=your_key          # Google Speech
```

详细文档：[ASR_COMPLETE.md](ASR_COMPLETE.md)

## 特性速览
- **配置热加载**：`ConfigWatcher` 配合 watchfiles 实时刷新 TOML 配置
- **模型网关**：已接入 `openai`(Chat Completions 兼容)、`vllm`(OpenAI兼容)、`ollama`、`hf`(本地 Qwen/Llama)、`gemini`，可通过前缀/别名路由
- **外接思维链 (CoT)**：为不支持原生思维链的模型（Qwen、Kimi、GLM、DeepSeek等）提供外接 Chain-of-Thought 功能，通过提示工程引导逐步推理
- **TTS语音合成**：支持Minimax、Azure、Google、Edge TTS，让AI会说话
- **ASR语音识别**：支持Whisper、Azure、Google、Faster-Whisper，让AI听懂人话
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