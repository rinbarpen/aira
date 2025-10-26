#!/bin/bash
# AIRA 桌面前端安装脚本

echo "🚀 开始安装 AIRA 桌面前端依赖..."

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ 错误: 未找到 uv 命令"
    echo "请先安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ 检测到 uv"

# 同步基础依赖
echo "📦 安装基础依赖..."
uv sync

# 安装桌面前端依赖
echo "🖥️  安装桌面前端依赖..."
uv sync --extra desktop

echo ""
echo "✨ 安装完成！"
echo ""
echo "使用方法："
echo "1. 启动后端服务:"
echo "   uv run uvicorn aira.server.api:create_app --factory --reload"
echo ""
echo "2. 启动桌面应用:"
echo "   uv run python run_desktop.py"
echo ""
echo "详细文档请查看 README_DESKTOP.md"

