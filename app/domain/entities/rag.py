from dataclasses import dataclass, field
from typing import Any, Literal

FusionStrategy = Literal["rrf", "weighted_score"]


@dataclass(frozen=True)
class RagDocument:
    text: str
    agent_id: str
    embedding_name: str
    embedding_id: str | None = None
    extra_fields: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RagChunk:
    text: str
    raw_text: str
    dense_embedding: list[float]
    agent_id: str
    embedding_name: str
    embedding_id: str
    extra_fields: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RagSearchOptions:
    k: int = 15
    dense_weight: float = 0.7
    sparse_weight: float = 0.3
    use_hybrid: bool = True
    relevance_boost: float = 1.5
    candidate_multiplier: int = 4
    candidate_top_k: int | None = None
    dense_ef_search: int = 128
    sparse_drop_ratio_search: float = 0.2
    fusion_strategy: FusionStrategy = "rrf"
    rrf_k: int = 60
    max_chunks_per_document: int | None = None


@dataclass(frozen=True)
class RagSearchResult:
    id: str
    score: float
    text: str
    agent_id: str
    embedding_name: str
    embedding_id: str
    extra_fields: dict[str, Any] = field(default_factory=dict)
    dense_score: float | None = None
    sparse_score: float | None = None
