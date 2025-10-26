"""主题和样式系统。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    """主题配置。"""
    
    name: str
    background: str
    foreground: str
    primary: str
    secondary: str
    accent: str
    user_bubble: str
    assistant_bubble: str
    border: str
    hover: str
    text: str
    text_secondary: str


# 预定义主题
THEMES: Dict[str, Theme] = {
    "light": Theme(
        name="浅色",
        background="#FFFFFF",
        foreground="#F5F5F5",
        primary="#2196F3",
        secondary="#FFC107",
        accent="#FF5722",
        user_bubble="#DCF8C6",
        assistant_bubble="#FFFFFF",
        border="#E0E0E0",
        hover="#F0F0F0",
        text="#000000",
        text_secondary="#666666",
    ),
    "dark": Theme(
        name="深色",
        background="#1E1E1E",
        foreground="#2D2D2D",
        primary="#0D47A1",
        secondary="#F57C00",
        accent="#D32F2F",
        user_bubble="#005C4B",
        assistant_bubble="#2D2D2D",
        border="#3E3E3E",
        hover="#3E3E3E",
        text="#FFFFFF",
        text_secondary="#AAAAAA",
    ),
    "blue": Theme(
        name="蓝色",
        background="#E3F2FD",
        foreground="#BBDEFB",
        primary="#1976D2",
        secondary="#64B5F6",
        accent="#0D47A1",
        user_bubble="#90CAF9",
        assistant_bubble="#FFFFFF",
        border="#42A5F5",
        hover="#BBDEFB",
        text="#000000",
        text_secondary="#555555",
    ),
    "green": Theme(
        name="绿色",
        background="#E8F5E9",
        foreground="#C8E6C9",
        primary="#388E3C",
        secondary="#66BB6A",
        accent="#1B5E20",
        user_bubble="#A5D6A7",
        assistant_bubble="#FFFFFF",
        border="#4CAF50",
        hover="#C8E6C9",
        text="#000000",
        text_secondary="#555555",
    ),
    "purple": Theme(
        name="紫色",
        background="#F3E5F5",
        foreground="#E1BEE7",
        primary="#7B1FA2",
        secondary="#BA68C8",
        accent="#4A148C",
        user_bubble="#CE93D8",
        assistant_bubble="#FFFFFF",
        border="#9C27B0",
        hover="#E1BEE7",
        text="#000000",
        text_secondary="#555555",
    ),
    "warm": Theme(
        name="暖色",
        background="#FFF3E0",
        foreground="#FFE0B2",
        primary="#E64A19",
        secondary="#FF9800",
        accent="#BF360C",
        user_bubble="#FFCC80",
        assistant_bubble="#FFFFFF",
        border="#FF5722",
        hover="#FFE0B2",
        text="#000000",
        text_secondary="#555555",
    ),
}


class ThemeManager:
    """主题管理器。"""

    def __init__(self, default_theme: str = "light") -> None:
        """初始化主题管理器。
        
        Args:
            default_theme: 默认主题名称
        """
        self.current_theme = THEMES.get(default_theme, THEMES["light"])

    def set_theme(self, theme_name: str) -> Theme:
        """设置主题。
        
        Args:
            theme_name: 主题名称
            
        Returns:
            主题对象
        """
        self.current_theme = THEMES.get(theme_name, THEMES["light"])
        return self.current_theme

    def get_stylesheet(self) -> str:
        """获取当前主题的样式表。
        
        Returns:
            Qt样式表字符串
        """
        theme = self.current_theme
        
        return f"""
        QMainWindow {{
            background-color: {theme.background};
            color: {theme.text};
        }}
        
        QWidget {{
            background-color: {theme.background};
            color: {theme.text};
        }}
        
        QTextEdit, QLineEdit {{
            background-color: {theme.foreground};
            color: {theme.text};
            border: 1px solid {theme.border};
            border-radius: 4px;
            padding: 5px;
        }}
        
        QPushButton {{
            background-color: {theme.primary};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {theme.accent};
        }}
        
        QPushButton:pressed {{
            background-color: {theme.secondary};
        }}
        
        QPushButton:disabled {{
            background-color: {theme.border};
            color: {theme.text_secondary};
        }}
        
        QComboBox {{
            background-color: {theme.foreground};
            color: {theme.text};
            border: 1px solid {theme.border};
            border-radius: 4px;
            padding: 5px;
        }}
        
        QComboBox:hover {{
            border-color: {theme.primary};
        }}
        
        QComboBox::drop-down {{
            border: none;
        }}
        
        QLabel {{
            color: {theme.text};
        }}
        
        QTabWidget::pane {{
            border: 1px solid {theme.border};
            background-color: {theme.background};
        }}
        
        QTabBar::tab {{
            background-color: {theme.foreground};
            color: {theme.text};
            border: 1px solid {theme.border};
            padding: 8px 16px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {theme.primary};
            color: white;
        }}
        
        QTabBar::tab:hover {{
            background-color: {theme.hover};
        }}
        
        QScrollBar:vertical {{
            background-color: {theme.foreground};
            width: 12px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {theme.border};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {theme.primary};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QGroupBox {{
            border: 1px solid {theme.border};
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
        }}
        
        QGroupBox::title {{
            color: {theme.primary};
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }}
        
        QStatusBar {{
            background-color: {theme.foreground};
            color: {theme.text};
            border-top: 1px solid {theme.border};
        }}
        
        QListWidget {{
            background-color: {theme.foreground};
            color: {theme.text};
            border: 1px solid {theme.border};
            border-radius: 4px;
        }}
        
        QListWidget::item:selected {{
            background-color: {theme.primary};
            color: white;
        }}
        
        QListWidget::item:hover {{
            background-color: {theme.hover};
        }}
        """

    def get_bubble_style(self, is_user: bool) -> str:
        """获取消息气泡样式。
        
        Args:
            is_user: 是否为用户消息
            
        Returns:
            样式字符串
        """
        theme = self.current_theme
        
        if is_user:
            return f"""
                background-color: {theme.user_bubble};
                border-radius: 10px;
                padding: 8px;
                margin: 4px;
                color: {theme.text};
            """
        else:
            return f"""
                background-color: {theme.assistant_bubble};
                border: 1px solid {theme.border};
                border-radius: 10px;
                padding: 8px;
                margin: 4px;
                color: {theme.text};
            """

    @staticmethod
    def get_available_themes() -> list[str]:
        """获取可用主题列表。
        
        Returns:
            主题名称列表
        """
        return list(THEMES.keys())

    @staticmethod
    def get_theme_display_names() -> dict[str, str]:
        """获取主题显示名称。
        
        Returns:
            主题ID到显示名称的映射
        """
        return {key: theme.name for key, theme in THEMES.items()}

