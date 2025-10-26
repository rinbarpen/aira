"""记忆服务占位实现。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from collections import deque

from aira.core.config import get_app_config
from aira.memory.repository import SqliteRepository
from aira.memory.vector_store import LocalVectorStore, VectorItem


@dataclass
class MemoryRecord:
    content: str
    category: str
    score: float
    metadata: dict[str, Any]


class MemoryService:
    """组合短期与长期记忆的服务。"""

    def __init__(self) -> None:
        self._short_term: dict[str, deque[MemoryRecord]] = {}
        config = get_app_config()
        self._window = int(config["memory"].get("short_term_window", 12))
        storage = config.get("storage", {})
        sqlite_path = Path(storage.get("sqlite_path", "data/aira.db"))
        index_path = Path(storage.get("vector_index_path", "data/vector.idx"))
        model = storage.get("embedding_model", "BAAI/bge-m3")
        self._repo = SqliteRepository(sqlite_path)
        self._vstore = LocalVectorStore(dim=None, index_path=index_path, model_name=model)

    async def fetch_recent(self, session_id: str, limit: int | None = None) -> Sequence[MemoryRecord]:
        window = self._short_term.get(session_id)
        if not window:
            return []
        limit = limit or self._window
        return list(window)[-limit:]

    async def search(self, query: str, persona_id: str, limit: int = 5) -> Sequence[MemoryRecord]:
        ids = self._vstore.search(query, k=limit)
        rows = await self._repo.fetch_memories_by_ids(ids)
        return [MemoryRecord(content=r.content, category=r.category, score=r.score, metadata={}) for r in rows]

    async def store(self, session_id: str, record: MemoryRecord) -> None:
        window = self._short_term.setdefault(session_id, deque(maxlen=self._window))
        window.append(record)
        # 写入 SQLite
        mem_id = await self._repo.insert_memory(session_id, record.category, record.content, record.score)
        # 加入向量索引
        self._vstore.add([VectorItem(id=mem_id, text=record.content)])

    async def add_conversation(
        self,
        session_id: str,
        role: str,
        content: str,
        *,
        model: str | None = None,
        provider: str | None = None,
        thought: str | None = None,
    ) -> int:
        return await self._repo.insert_conversation(
            session_id,
            role,
            content,
            model=model,
            provider=provider,
            thought=thought,
        )

