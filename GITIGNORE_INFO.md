# Git 和 Cursor 忽略配置说明

## 已配置的忽略文件

### `.gitignore`
Git 版本控制忽略文件，以下类型的文件不会被提交：

#### Python 相关
- `__pycache__/` - Python 字节码缓存
- `*.pyc, *.pyo, *.pyd` - 编译的 Python 文件
- `*.egg-info/` - 包信息
- `build/, dist/` - 构建输出

#### 虚拟环境
- `venv/, .venv/, env/` - Python 虚拟环境

#### 数据文件
- `data/` - 所有数据文件目录
- `*.db, *.sqlite, *.sqlite3` - 数据库文件
- `data/conversations.db` - 对话历史数据库
- `data/audio/*.wav` - 录音文件
- `uploads/` - 用户上传的文件

#### ASR 模型
- `models/` - 下载的模型文件
- `.cache/` - 模型缓存
- `*.pt, *.bin` - PyTorch 模型文件

#### 日志文件
- `logs/` - 日志目录
- `*.log` - 所有日志文件

#### 临时文件
- `tmp/, temp/` - 临时目录
- `*.tmp, *.bak` - 临时备份文件

#### 配置覆盖
- `config/local*.toml` - 本地配置文件

#### 大型媒体文件
- `*.mp4, *.avi, *.mov` - 视频文件
- `*.wav, *.flac` - 无损音频文件

---

### `.cursorignore`
Cursor AI 索引忽略文件，以下文件不会被 AI 分析：

#### 为什么需要 .cursorignore？
1. **提高性能** - 避免索引大文件和二进制文件
2. **减少噪音** - 排除数据文件和缓存
3. **保护隐私** - 不索引用户数据和对话记录
4. **节省资源** - 不处理模型文件和依赖锁文件

#### 主要忽略内容
- 所有 `.gitignore` 中的内容
- `uv.lock, requirements.lock` - 大型依赖锁文件
- `*.safetensors, *.ckpt` - 大型模型文件
- `docs/_build/` - 文档构建输出

---

## 目录结构

项目中会创建以下目录（仅保留结构，不提交内容）：

```
aira/
├── data/                    # 数据目录（被忽略）
│   ├── .gitkeep            # 保持目录存在
│   ├── conversations.db    # SQLite 数据库（被忽略）
│   └── audio/              # 音频文件（被忽略）
│       ├── .gitkeep
│       └── *.wav           # 录音文件（被忽略）
├── uploads/                # 上传文件（被忽略）
│   └── .gitkeep
├── logs/                   # 日志文件（被忽略）
│   └── *.log
└── models/                 # 模型文件（被忽略）
    └── whisper-*
```

---

## 使用建议

### 1. 查看被忽略的文件
```bash
# 查看 git 状态（忽略文件不会显示）
git status

# 查看所有文件（包括被忽略的）
git status --ignored
```

### 2. 强制添加被忽略的文件
如果确实需要添加某个被忽略的文件：
```bash
git add -f <file>
```

### 3. 清理被忽略的文件
```bash
# 删除所有被忽略的文件（小心使用）
git clean -fdX

# 预览会删除什么
git clean -ndX
```

### 4. 测试忽略规则
```bash
# 测试某个文件是否被忽略
git check-ignore -v <file>
```

---

## 常见问题

### Q: 为什么对话历史不被提交？
A: 对话历史包含用户隐私数据，应该只保存在本地。每个用户应该有自己的对话记录。

### Q: 如何备份数据？
A: 可以手动备份 `data/` 目录：
```bash
tar -czf aira_data_backup_$(date +%Y%m%d).tar.gz data/
```

### Q: ASR 模型文件在哪里？
A: 首次使用时会自动下载到缓存目录（通常在 `~/.cache/huggingface/`），这些文件被忽略。

### Q: 如何清理旧的录音文件？
A: 录音文件在 `data/audio/` 目录，可以手动删除：
```bash
rm -f data/audio/*.wav
```

---

## 更新忽略规则

如果需要修改忽略规则：

1. 编辑 `.gitignore` 或 `.cursorignore`
2. 如果文件已经被 git 跟踪，需要先移除：
```bash
git rm --cached <file>
git commit -m "Remove tracked file"
```

---

## 提交时的最佳实践

### 应该提交的文件
✅ 源代码（`.py` 文件）
✅ 配置模板（`config/*.toml`）
✅ 文档（`*.md`, `docs/`）
✅ 测试文件（`tests/`）
✅ 依赖配置（`pyproject.toml`）
✅ 安装脚本（`*.sh`）

### 不应该提交的文件
❌ 数据库文件（`*.db`）
❌ 用户数据（`data/`, `uploads/`）
❌ 日志文件（`*.log`）
❌ 临时文件（`*.tmp`, `*.bak`）
❌ 虚拟环境（`venv/`, `.venv/`）
❌ Python 缓存（`__pycache__/`）
❌ 模型文件（`*.pt`, `*.bin`）
❌ 大型媒体文件（`*.mp4`, `*.wav`）
❌ 本地配置（`config/local*.toml`）

---

**配置日期**: 2025-10-26  
**版本**: 1.0

