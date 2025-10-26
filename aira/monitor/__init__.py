from __future__ import annotations

from dataclasses import dataclass

from aira.memory.repository import SqliteRepository


@dataclass
class Pricing:
    input_per_million: float  # USD per 1M tokens
    output_per_million: float


class Monitor:
    def __init__(self, repo: SqliteRepository, pricing_table: dict[str, Pricing]) -> None:
        self._repo = repo
        self._pricing = pricing_table

    def estimate_cost(self, model: str, tokens_in: int, tokens_out: int) -> float:
        p = self._pricing.get(model)
        if not p:
            # fallback: $0
            return 0.0
        return (tokens_in * p.input_per_million + tokens_out * p.output_per_million) / 1_000_000.0

    async def record(
        self,
        *,
        request_id: str,
        session_id: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        duration_ms: float,
    ) -> int:
        cost = self.estimate_cost(model, tokens_in, tokens_out)
        return await self._repo.insert_usage(
            request_id=request_id,
            session_id=session_id,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost,
            duration_ms=duration_ms,
        )


