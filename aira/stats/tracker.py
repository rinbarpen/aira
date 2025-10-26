"""统计计量模块实现。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any, Iterable


@dataclass
class StatRecord:
    request_id: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_estimate: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class Timer:
    def __enter__(self) -> "Timer":
        self.start = monotonic()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        self.duration = monotonic() - self.start

    async def __aenter__(self) -> "Timer":
        self.start = monotonic()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        self.duration = monotonic() - self.start


class StatsTracker:
    def __init__(self, log_path: str | Path | None = None) -> None:
        self._records: list[StatRecord] = []
        self._log_path = Path(log_path or "data/stats.jsonl")
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, stat: StatRecord) -> None:
        self._records.append(stat)
        self._append_to_log(stat)

    def bulk_record(self, stats: Iterable[StatRecord]) -> None:
        for stat in stats:
            self.record(stat)

    def timer(self) -> Timer:
        return Timer()

    def list(self) -> list[StatRecord]:
        return list(self._records)

    def _append_to_log(self, stat: StatRecord) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": stat.request_id,
            "model": stat.model,
            "tokens_in": stat.tokens_in,
            "tokens_out": stat.tokens_out,
            "cost_estimate": stat.cost_estimate,
            "extra": stat.extra,
        }
        with self._log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


_GLOBAL_TRACKER: StatsTracker | None = None


def get_tracker() -> StatsTracker:
    global _GLOBAL_TRACKER
    if _GLOBAL_TRACKER is None:
        _GLOBAL_TRACKER = StatsTracker()
    return _GLOBAL_TRACKER

