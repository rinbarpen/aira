"""本地对话历史存储。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class ConversationStorage:
    """对话历史本地存储。"""

    def __init__(self, db_path: str = "data/conversations.db") -> None:
        """初始化存储。
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """初始化数据库表。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    persona_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_type TEXT DEFAULT 'text',
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_session (session_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    persona_id TEXT NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()

    def save_message(
        self,
        session_id: str,
        persona_id: str,
        role: str,
        content: str,
        content_type: str = "text",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """保存消息。
        
        Args:
            session_id: 会话ID
            persona_id: 角色ID
            role: 角色（user/assistant）
            content: 消息内容
            content_type: 内容类型（text/image/audio/document）
            metadata: 元数据
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO conversations (session_id, persona_id, role, content, content_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, persona_id, role, content, content_type, json.dumps(metadata or {}))
            )
            
            # 更新会话时间
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions (session_id, persona_id, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (session_id, persona_id)
            )
            
            conn.commit()

    def get_conversation(self, session_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """获取对话历史。
        
        Args:
            session_id: 会话ID
            limit: 返回消息数量限制
            
        Returns:
            消息列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM conversations
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (session_id, limit)
            )
            
            messages = []
            for row in cursor:
                messages.append({
                    "id": row["id"],
                    "role": row["role"],
                    "content": row["content"],
                    "content_type": row["content_type"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "created_at": row["created_at"],
                })
            
            return list(reversed(messages))

    def get_sessions(self, limit: int = 50) -> list[dict[str, Any]]:
        """获取会话列表。
        
        Args:
            limit: 返回数量限制
            
        Returns:
            会话列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM sessions
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            
            return [dict(row) for row in cursor]

    def delete_conversation(self, session_id: str) -> None:
        """删除对话历史。
        
        Args:
            session_id: 会话ID
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()

    def update_session_title(self, session_id: str, title: str) -> None:
        """更新会话标题。
        
        Args:
            session_id: 会话ID
            title: 标题
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE sessions SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (title, session_id)
            )
            conn.commit()

    def search_conversations(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """搜索对话。
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            匹配的消息列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM conversations
                WHERE content LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (f"%{query}%", limit)
            )
            
            return [dict(row) for row in cursor]

