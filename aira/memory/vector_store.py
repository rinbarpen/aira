from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import hnswlib  # type: ignore
from fastembed import TextEmbedding

from aira.core.config import get_app_config


@dataclass
class VectorItem:
    id: int
    text: str


class LocalVectorStore:
    def __init__(self, dim: int | None, index_path: Path, model_name: str) -> None:
        self._index_path = index_path
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        hardware_cfg = get_app_config().get("hardware", {})
        use_gpu = hardware_cfg.get("use_gpu", False)
        provider = "CUDAExecutionProvider" if use_gpu else "CPUExecutionProvider"
        self._model = TextEmbedding(model_name, providers=[provider])
        probe_vector = list(self._model.embed(["probe zh 中文 ja 日本語 en English"]))[0]
        derived_dim = len(probe_vector)
        if dim is not None and dim != derived_dim:
            raise ValueError(f"指定的 dim={dim} 与模型实际维度 {derived_dim} 不一致")
        self._dim = dim or derived_dim
        self._index = hnswlib.Index(space="cosine", dim=self._dim)
        self._initialized = False

    def _ensure(self) -> None:
        if self._initialized:
            return
        if self._index_path.exists():
            self._index.load_index(str(self._index_path))
        else:
            self._index.init_index(max_elements=10000, ef_construction=200, M=16)
        self._index.set_ef(50)
        self._initialized = True

    def _encode(self, texts: list[str]) -> list[list[float]]:
        return list(self._model.embed(texts))

    def add(self, items: list[VectorItem]) -> None:
        self._ensure()
        vectors = self._encode([it.text for it in items])
        ids = [it.id for it in items]
        self._index.add_items(vectors, ids)
        self._index.save_index(str(self._index_path))

    def search(self, query: str, k: int = 5) -> list[int]:
        self._ensure()
        qv = self._encode([query])[0]
        labels, _ = self._index.knn_query([qv], k=k)
        return list(map(int, labels[0]))

