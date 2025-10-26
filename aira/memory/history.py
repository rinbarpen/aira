from __future__ import annotations

from dataclasses import dataclass

from aira.memory.repository import SqliteRepository


@dataclass
class BranchHead:
    session_id: str
    branch: str


class ChatHistoryManager:
    def __init__(self, repo: SqliteRepository) -> None:
        self._repo = repo

    async def append(self, session_id: str, role: str, content: str, branch: str = "main") -> int:
        return await self._repo.insert_conversation(session_id, role, content, branch)

    async def recent(self, session_id: str, limit: int = 12, branch: str = "main"):
        return await self._repo.fetch_recent_conversations(session_id, limit, branch)


