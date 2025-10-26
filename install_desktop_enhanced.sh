#!/bin/bash
# AIRA 桌面前端增强版安装脚本

echo "🚀 开始安装 AIRA 桌面前端增强版..."
echo ""

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ 错误: 未找到 uv 命令"
    echo "请先安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ 检测到 uv"
echo ""

# 检查系统依赖
echo "🔍 检查系统依赖..."

# 检查 PortAudio（用于 pyaudio）
if ! ldconfig -p 2>/dev/null | grep -q portaudio; then
    echo "⚠️  警告: 未检测到 PortAudio 库"
    echo ""
    echo "PyAudio 需要 PortAudio 系统库。请运行："
    echo ""
    if [[ -f /etc/debian_version ]]; then
        echo "  sudo apt-get update"
        echo "  sudo apt-get install portaudio19-dev"
    elif [[ -f /etc/redhat-release ]]; then
        echo "  sudo dnf install portaudio-devel"
    elif [[ -f /etc/arch-release ]]; then
        echo "  sudo pacman -S portaudio"
    else
        echo "  请查看 INSTALL_DEPENDENCIES.md 了解详细说明"
    fi
    echo ""
    read -p "是否继续安装？(语音功能将不可用) [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "安装已取消"
        exit 1
    fi
else
    echo "✅ 检测到 PortAudio 库"
fi

echo ""

# 同步基础依赖
echo "📦 安装基础依赖..."
uv sync

echo ""

# 安装桌面前端依赖
echo "🖥️  安装桌面前端增强版依赖..."
echo "这将安装以下包:"
echo "  - PyQt6 (GUI 框架)"
echo "  - qasync (异步支持)"
echo "  - aiofiles (异步文件操作)"
echo "  - pillow (图像处理)"
echo "  - pyaudio (音频录制)"
echo "  - soundfile (音频文件)"
echo "  - faster-whisper (语音识别)"
echo ""

uv sync --extra desktop

echo ""
echo "✨ 安装完成！"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 AIRA 桌面前端增强版 v0.2.0"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌟 新功能:"
echo "  ✅ 流式响应"
echo "  ✅ 本地存储"
echo "  ✅ 图像支持"
echo "  ✅ 语音消息"
echo "  ✅ ASR 识别"
echo "  ✅ 文档上传"
echo "  ✅ 自定义主题"
echo "  ✅ 便捷回复"
echo "  ✅ 多语言"
echo ""
echo "使用方法："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  启动后端服务:"
echo "   uv run uvicorn aira.server.api:create_app --factory --reload"
echo ""
echo "2️⃣  启动桌面应用:"
echo "   基础版: uv run python run_desktop.py"
echo "   增强版: uv run python run_desktop_enhanced.py  👈 推荐"
echo ""
echo "📚 详细文档："
echo "   - 基础版: README_DESKTOP.md"
echo "   - 增强版: README_DESKTOP_ENHANCED.md"
echo "   - 功能总结: ENHANCED_FEATURES_SUMMARY.md"
echo ""
echo "💡 提示："
echo "   - 首次使用 ASR 功能时会下载模型"
echo "   - 建议使用 'base' 模型（平衡）"
echo "   - 可在设置中自定义主题和功能"
echo ""
echo "享受全新的 AIRA 体验！🎉"

