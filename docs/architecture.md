# AIRA 持续对话机器人设计方案

## 1. 目标与范围
- 构建支持多模型、持久记忆、角色扮演的智能对话后端
- 提供统一 API 与 CLI 接口，便于在产品化场景中集成
- 支持 MCP Server、工具插件体系以及 token/推理时间统计
- 默认角色设定为“可塑性记忆的艾拉”，并可通过配置动态扩展

## 2. 整体架构
- **接入层**：RESTful API（FastAPI/Starlette）与 CLI（Typer），共享核心服务
- **对话编排层**：会话控制器负责意图识别、上下文拼接、模型路由、工具调用编排
- **模型接入层**：统一 Model Adapter 接口，针对 Gemini、GPT、Claude、Qwen、Kimi、DeepSeek、OpenRouter 等模型实现适配器
- **记忆层**：短期上下文缓存 + 长期记忆存储（向量数据库 / KV 存储），提供记忆检索与写入策略
- **插件层**：Tools Plugin Manager，实现工具注册、鉴权、调用协议；提供本地工具、MCP Server 工具两类
- **统计与监控**：Token 计费、推理耗时、调用链日志、错误追踪
- **配置与角色管理**：TOML 配置驱动角色/插件/模型策略；支持动态热更新与版本化
- **基础设施**：使用 `uv` 管理 Python 依赖与虚拟环境，容器化部署（可选）

## 3. 关键模块
### 3.1 会话控制器 `DialogueOrchestrator`
- 维护会话状态机，处理用户输入，协调记忆检索、角色上下文、工具调用
- 支持多轮对话、并发会话，提供优雅的降级策略（模型超时、工具失败）

### 3.2 记忆系统
- **短期记忆**：最近 N 轮对话缓存，快速拼接上下文
- **长期记忆**：
  - 结构化记忆库（PostgreSQL/SQLite）保存事实类信息
  - 向量库（Milvus/Faiss/pgvector）按 embedding（OpenAI/Local 模型）检索相似内容
- **记忆策略**：
  - 写入策略：置信度阈值 + 记忆分类（事实、情绪、偏好）
  - 读取策略：检索得分 + 时效性加权
- **可塑性记忆**：根据角色配置调整检索/写入权重，实现“艾拉”个性化记忆

### 3.3 模型适配层 `ModelGateway`
- 提供统一接口：`generate`, `stream_generate`, `count_tokens`
- 模型支持能力矩阵：

| 模型 | 文本生成 | 代码生成 | 图像生成 | 视频生成 | 多模态理解 | 思考模式 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gemini 1.5 | ✅ | ✅ | ✅ | ⚠️（有限） | ✅ | 思维链可控 | 需 Google API Key |
| GPT-4.1/4o | ✅ | ✅ | ✅（DALLE via OpenAI） | ❌ | ✅ | CoT/Tree-of-Thought | OpenAI API |
| Claude 3.5 | ✅ | ✅ | ❌ | ❌ | ✅ | Constitutional AI | Anthropic API |
| Qwen 2.5 | ✅ | ✅ | ✅（Qwen-VL） | ⚠️（研究中） | ✅ | 工程模式 | 阿里百炼 |
| Kimi Moonshot | ✅ | ✅ | ✅（内测） | ❌ | ✅ | 长文本 | Moonshot API |
| Deepseek V2 | ✅ | ✅ | ❌ | ❌ | ✅ | 推理增强 | Deepseek API |
| OpenRouter | ✅ | ✅ | ✅（取决于路由模型） | ⚠️ | ✅ | 聚合模式 | 按路由模型收敛 |

- 适配器负责：鉴权凭证管理、请求签名、流式解析、错误分类重试
- 支持模型能力标记，供编排层做智能路由

### 3.4 工具插件与 MCP 支持
- 使用统一的 Tool Schema（基于 JSON Schema）描述输入输出
- **本地工具**：Python 函数或外部命令，通过装饰器注册
- **MCP Server**：
  - 实现 MCP Client（依照 Model Context Protocol），支持 Capabilities 协商
  - 将 MCP 工具暴露给编排层，支持执行、订阅事件
- 插件管理：
  - 插件仓库目录扫描 + TOML 描述
  - 动态加载、版本兼容校验、权限管理
  - 失败隔离与熔断

### 3.5 角色与配置
- 主配置文件：`config/aira.toml`
  - `persona`：角色基础设定（名称、背景、语气、价值观、记忆策略）
  - `memory`：参数（短期窗口长度、向量模型、阈值）
  - `models`：默认模型、备选模型、降级策略
  - `tools`：启用/禁用、授权范围、MCP 地址
- 角色切换：读取 TOML，热加载；默认 `Aira`（可塑性记忆）
- 场景预设：支持以 `profiles/{scene}.toml` 存储特定任务角色

## 4. 数据流与时序
1. 输入到达 API/CLI -> 会话控制器根据会话 ID 加载上下文
2. 调用记忆服务检索短期、长期记忆
3. Persona Manager 注入角色前置提示与行为规范
4. 路由模型：根据配置与任务类型选择模型，必要时调用工具
5. 工具调用采用回合式 Planner：
   - LLM 生成工具调用意图
   - 统一执行（本地或 MCP）
   - 返回结果合并进上下文
6. 生成最终回复，写入记忆、统计 token/时长，返回响应

## 5. API 与 CLI 设计
- **API**：
  - `POST /api/v1/chat`：标准对话（支持流式 SSE/WebSocket）
  - `POST /api/v1/memory`：写入/更新记忆
  - `GET /api/v1/memory`：检索记忆
  - `GET /api/v1/stats`：查询 token/耗时统计
  - `POST /api/v1/tools/invoke`：直接调用工具
  - `POST /api/v1/persona/reload`：热更新角色
- **CLI**（基于 Typer）：
  - `aira chat --session <id>`
  - `aira persona list|use`
  - `aira memory add|search`
  - `aira tools invoke`
  - `aira stats show`

## 6. 统计与监控
- **Token 统计**：
  - 统一使用模型返回的 usage 字段；若无则通过 tokenizer 估算
  - 记录请求 ID、模型、输入/输出 token、费用估算
- **耗时统计**：
  - 记录编排总耗时、模型推理耗时、工具执行耗时
  - Prometheus + Grafana（可选）
- **日志/审计**：按会话 ID 存储，遵守隐私规范，支持脱敏

## 7. 技术栈与工程实践
- 语言：Python 3.11+，使用 `uv` 管理依赖
- Web 框架：FastAPI；异步任务：AnyIO
- 数据层：PostgreSQL + Redis + 向量库；使用 SQLAlchemy/Prisma
- 消息队列（可选）：用于异步任务（工具耗时操作）
- 测试：Pytest + VCR/Responses 模拟外部模型
- 部署：Dockerfile + Compose；支持 Kubernetes

## 8. 开发路线建议
1. **MVP**：实现会话控制器、OpenAI 模型接入、短期记忆、CLI、token 统计
2. **记忆增强**：引入向量检索、长期记忆策略
3. **插件与 MCP**：工具框架、MCP Client、插件管理
4. **多模型支持**：逐步接入 Gemini、Claude、Qwen 等
5. **角色系统**：TOML 配置、Persona Manager、默认 Aira
6. **监控与优化**：耗时、费用、并发扩展、容错

## 9. 风险与注意事项
- 多模型鉴权管理需安全加密（Key Vault）
- 记忆隐私与合规要求（GDPR/数据脱敏）
- MCP 工具执行需沙箱隔离，避免供应商兼容问题
- 模型能力差异需在路由层显式声明，避免误用
- Token 统计准确度需结合官方接口与本地估算

## 10. 下一步工作
- 梳理配置文件模板与目录结构
- 搭建 `uv` 项目骨架，初始化核心模块包
- 设计测试样例与自动化流程

