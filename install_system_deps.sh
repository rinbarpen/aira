#!/bin/bash
# 安装 AIRA 桌面前端所需的系统依赖

echo "📦 安装 AIRA 系统依赖..."
echo ""

# 检测系统类型
if [[ -f /etc/debian_version ]]; then
    # Debian/Ubuntu
    echo "检测到 Debian/Ubuntu 系统"
    echo ""
    echo "即将安装："
    echo "  - portaudio19-dev (用于音频录制)"
    echo ""
    
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev
    
    echo ""
    echo "✅ 系统依赖安装完成！"
    
elif [[ -f /etc/redhat-release ]]; then
    # Fedora/RHEL/CentOS
    echo "检测到 RedHat 系列系统"
    echo ""
    
    sudo dnf install -y portaudio-devel
    
    echo ""
    echo "✅ 系统依赖安装完成！"
    
elif [[ -f /etc/arch-release ]]; then
    # Arch Linux
    echo "检测到 Arch Linux 系统"
    echo ""
    
    sudo pacman -S --noconfirm portaudio
    
    echo ""
    echo "✅ 系统依赖安装完成！"
    
else
    echo "⚠️  无法自动检测系统类型"
    echo ""
    echo "请手动安装 PortAudio 开发库："
    echo "  - Ubuntu/Debian: sudo apt-get install portaudio19-dev"
    echo "  - Fedora/RHEL: sudo dnf install portaudio-devel"
    echo "  - Arch: sudo pacman -S portaudio"
    echo "  - macOS: brew install portaudio"
    echo ""
    exit 1
fi

echo ""
echo "现在可以运行："
echo "  ./install_desktop_enhanced.sh"
echo "或："
echo "  uv sync --extra desktop"

