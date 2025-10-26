from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import aiosqlite


SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    branch TEXT NOT NULL DEFAULT 'main',
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    model TEXT,
    provider TEXT,
    thought TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    branch TEXT NOT NULL DEFAULT 'main',
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    score REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usage_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    model TEXT NOT NULL,
    tokens_in INTEGER NOT NULL,
    tokens_out INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    duration_ms REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


@dataclass
class ConversationRow:
    id: int
    session_id: str
    role: str
    content: str
    model: str | None
    provider: str | None
    thought: str | None


@dataclass
class MemoryRow:
    id: int
    session_id: str
    category: str
    content: str
    score: float


class SqliteRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_lock = asyncio.Lock()
        self._initialized = False

    async def ensure_schema(self) -> None:
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            async with aiosqlite.connect(self._db_path) as db:
                await db.executescript(SCHEMA)
                await db.commit()
            self._initialized = True

    async def insert_conversation(self, session_id: str, role: str, content: str, branch: str = "main", *, model: str | None = None, provider: str | None = None, thought: str | None = None) -> int:
        await self.ensure_schema()
        async with aiosqlite.connect(self._db_path) as db:
            cur = await db.execute(
                "INSERT INTO conversations(session_id, branch, role, content, model, provider, thought) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, branch, role, content, model, provider, thought),
            )
            await db.commit()
            return int(cur.lastrowid)

    async def insert_memory(self, session_id: str, category: str, content: str, score: float, branch: str = "main") -> int:
        await self.ensure_schema()
        async with aiosqlite.connect(self._db_path) as db:
            cur = await db.execute(
                "INSERT INTO memories(session_id, branch, category, content, score) VALUES (?, ?, ?, ?, ?)",
                (session_id, branch, category, content, score),
            )
            await db.commit()
            return int(cur.lastrowid)

    async def fetch_recent_conversations(self, session_id: str, limit: int, branch: str = "main") -> list[ConversationRow]:
        await self.ensure_schema()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT id, session_id, role, content, model, provider, thought FROM conversations WHERE session_id=? AND branch=? ORDER BY id DESC LIMIT ?",
                (session_id, branch, limit),
            )
            rows = await cur.fetchall()
        return [ConversationRow(**dict(r)) for r in rows][::-1]

    async def fetch_recent_memories(self, session_id: str, limit: int, branch: str = "main") -> list[MemoryRow]:
        await self.ensure_schema()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT id, session_id, category, content, score FROM memories WHERE session_id=? AND branch=? ORDER BY id DESC LIMIT ?",
                (session_id, branch, limit),
            )
            rows = await cur.fetchall()
        return [MemoryRow(**dict(r)) for r in rows][::-1]

    async def fetch_memories_by_ids(self, ids: Sequence[int]) -> list[MemoryRow]:
        if not ids:
            return []
        qmarks = ",".join(["?"] * len(ids))
        await self.ensure_schema()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                f"SELECT id, session_id, category, content, score FROM memories WHERE id IN ({qmarks})",
                tuple(int(i) for i in ids),
            )
            rows = await cur.fetchall()
        # 保持与传入 ids 顺序相同
        row_map = {int(r["id"]): MemoryRow(**dict(r)) for r in rows}
        return [row_map[i] for i in ids if i in row_map]

    async def insert_usage(
        self,
        *,
        request_id: str,
        session_id: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        cost_usd: float,
        duration_ms: float,
    ) -> int:
        await self.ensure_schema()
        async with aiosqlite.connect(self._db_path) as db:
            cur = await db.execute(
                """
                INSERT INTO usage_records(request_id, session_id, model, tokens_in, tokens_out, cost_usd, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (request_id, session_id, model, tokens_in, tokens_out, cost_usd, duration_ms),
            )
            await db.commit()
            return int(cur.lastrowid)


