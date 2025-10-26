from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class TodoItem:
    id: int
    content: str
    done: bool = False


class TodoManager:
    def __init__(self) -> None:
        self._items: list[TodoItem] = []
        self._next_id = 1

    def add(self, content: str) -> TodoItem:
        item = TodoItem(id=self._next_id, content=content)
        self._next_id += 1
        self._items.append(item)
        return item

    def list(self) -> list[TodoItem]:
        return list(self._items)

    def complete(self, item_id: int) -> TodoItem:
        for item in self._items:
            if item.id == item_id:
                item.done = True
                return item
        raise ValueError(f"Todo item {item_id} not found")


# 简易全局管理器
_MANAGER: TodoManager | None = None


def get_manager() -> TodoManager:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = TodoManager()
    return _MANAGER


def todo_add(content: str) -> dict[str, Any]:
    item = get_manager().add(content)
    return {"id": item.id, "content": item.content, "done": item.done}


def todo_list() -> dict[str, Any]:
    items = [item.__dict__ for item in get_manager().list()]
    return {"items": items}


def todo_complete(item_id: int) -> dict[str, Any]:
    item = get_manager().complete(item_id)
    return {"id": item.id, "content": item.content, "done": item.done}
