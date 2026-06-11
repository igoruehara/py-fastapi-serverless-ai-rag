from typing import Any, Protocol

from app.domain.entities.rag import RagChunk, RagSearchOptions, RagSearchResult


class RagVectorStorePort(Protocol):
    def create_collection(self, collection_name: str, embedding_dim: int) -> dict[str, Any]:
        raise NotImplementedError

    def create_index(self, collection_name: str) -> dict[str, Any]:
        raise NotImplementedError

    def add_chunks(self, collection_name: str, chunks: list[RagChunk]) -> dict[str, Any]:
        raise NotImplementedError

    def search_hybrid(
        self,
        collection_name: str,
        query: str,
        query_embedding: list[float],
        agent_id: str,
        options: RagSearchOptions,
        extra_filters: dict[str, Any] | None = None,
    ) -> list[RagSearchResult]:
        raise NotImplementedError
