from __future__ import annotations

import hashlib
import json
from typing import Any

from app.application.use_cases.chat import ChatUseCase
from app.domain.entities.llm import ChatMessage, ProviderName
from app.domain.entities.rag import RagChunk, RagDocument, RagSearchOptions, RagSearchResult
from app.domain.ports.embeddings import EmbeddingPort
from app.domain.ports.vector_store import RagVectorStorePort
from app.infrastructure.text.chunker import TextChunker
from app.infrastructure.text.extra_fields import normalize_extra_fields


class RagUseCase:
    def __init__(
        self,
        vector_store: RagVectorStorePort,
        embeddings: EmbeddingPort,
        chat_use_case: ChatUseCase,
        default_collection: str,
        embedding_dim: int,
    ) -> None:
        self._vector_store = vector_store
        self._embeddings = embeddings
        self._chat_use_case = chat_use_case
        self._default_collection = default_collection
        self._embedding_dim = embedding_dim

    def create_collection(
        self,
        collection_name: str | None = None,
        embedding_dim: int | None = None,
    ) -> dict[str, Any]:
        return self._vector_store.create_collection(
            collection_name=self._collection(collection_name),
            embedding_dim=embedding_dim or self._embedding_dim,
        )

    def create_index(self, collection_name: str | None = None) -> dict[str, Any]:
        return self._vector_store.create_index(collection_name=self._collection(collection_name))

    def embedding_create(self, text: str) -> dict[str, Any]:
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Text is required")
        embedding = self._embeddings.embed_text(clean_text)
        return {"embedding": embedding, "dimension": len(embedding)}

    def add_documents(
        self,
        documents: list[RagDocument],
        collection_name: str | None = None,
        chunk_size: int = 512,
        chunk_overlap: int = 70,
        batch_size: int = 100,
        deduplicate: bool = False,
        no_split: bool = False,
        no_header: bool = False,
    ) -> dict[str, Any]:
        if not documents:
            raise ValueError("At least one document is required")
        if chunk_size <= 0:
            raise ValueError("chunkSize must be greater than zero")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunkOverlap must be lower than chunkSize")

        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        collection = self._collection(collection_name)
        seen_hashes: set[str] = set()
        inserted = 0
        skipped_duplicates = 0
        total_chunks = 0
        buffer: list[RagChunk] = []

        def flush_buffer() -> None:
            nonlocal inserted, buffer
            if not buffer:
                return
            self._vector_store.add_chunks(collection_name=collection, chunks=buffer)
            inserted += len(buffer)
            buffer = []

        for document in documents:
            self._validate_document(document)
            extra_fields = normalize_extra_fields(document.extra_fields)
            raw_chunks = [document.text.strip()] if no_split else chunker.split_text(document.text)
            total = len(raw_chunks)

            for index, raw_chunk in enumerate(raw_chunks, start=1):
                clean_chunk = raw_chunk.strip()
                if not clean_chunk:
                    continue

                dedupe_key = self._dedupe_key(document.agent_id, clean_chunk)
                if deduplicate and dedupe_key in seen_hashes:
                    skipped_duplicates += 1
                    continue
                seen_hashes.add(dedupe_key)

                chunk_extra_fields = dict(extra_fields)
                chunk_extra_fields["part"] = f"{index}/{total}"
                embedding_id = document.embedding_id or self._embedding_id(document)
                enriched_text = clean_chunk
                if not no_header:
                    enriched_text = self._enrich_chunk(
                        text=clean_chunk,
                        extra_fields=extra_fields,
                        part=chunk_extra_fields["part"],
                    )

                dense_embedding = self._embeddings.embed_text(enriched_text)
                buffer.append(
                    RagChunk(
                        text=enriched_text,
                        raw_text=clean_chunk,
                        dense_embedding=dense_embedding,
                        agent_id=document.agent_id,
                        embedding_name=document.embedding_name,
                        embedding_id=embedding_id,
                        extra_fields=chunk_extra_fields,
                    )
                )
                total_chunks += 1

                if len(buffer) >= batch_size:
                    flush_buffer()

        flush_buffer()
        return {
            "collectionName": collection,
            "documents": len(documents),
            "chunks": total_chunks,
            "inserted": inserted,
            "skippedDuplicates": skipped_duplicates,
        }

    def search_hybrid(
        self,
        query: str,
        agent_id: str,
        collection_name: str | None = None,
        options: RagSearchOptions | None = None,
        extra_filters: dict[str, Any] | None = None,
    ) -> list[RagSearchResult]:
        clean_query = query.strip()
        clean_agent_id = agent_id.strip()
        if not clean_query:
            raise ValueError("Query is required")
        if not clean_agent_id:
            raise ValueError("agentId is required")

        search_options = options or RagSearchOptions()
        query_embedding = self._embeddings.embed_text(clean_query)
        return self._vector_store.search_hybrid(
            collection_name=self._collection(collection_name),
            query=clean_query,
            query_embedding=query_embedding,
            agent_id=clean_agent_id,
            options=search_options,
            extra_filters=normalize_extra_fields(extra_filters or {}),
        )

    def chat(
        self,
        text: str,
        agent_id: str,
        provider: ProviderName,
        model: str | None,
        collection_name: str | None = None,
        system_prompt: str | None = None,
        params: dict[str, Any] | None = None,
        extra_filters: dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Text is required")

        params = params or {}
        search_options = rag_search_options_from_dict(params)
        docs: list[RagSearchResult] = []
        context: str | None = None

        if search_options.k > 0:
            docs = self.search_hybrid(
                query=clean_text,
                agent_id=agent_id,
                collection_name=collection_name,
                options=search_options,
                extra_filters=extra_filters,
            )
            context = self._context_from_docs(docs)

        response = self._chat_use_case.execute(
            provider=provider,
            model=model,
            messages=[ChatMessage(role="user", content=clean_text)],
            system_prompt=system_prompt,
            context=context,
            temperature=temperature if temperature is not None else params.get("temperature"),
            max_tokens=max_tokens if max_tokens is not None else params.get("maxTokens"),
            extra={"rag": {"enabled": bool(docs), "documents": len(docs)}},
        )
        return {
            "text": response.text,
            "provider": response.provider,
            "model": response.model,
            "usage": response.usage,
            "rag": {
                "enabled": bool(docs),
                "collectionName": self._collection(collection_name),
                "documents": [rag_result_to_dict(doc) for doc in docs],
            },
        }

    def _collection(self, collection_name: str | None) -> str:
        collection = (collection_name or self._default_collection or "").strip()
        if not collection:
            raise ValueError("collectionName is required")
        return collection

    def _validate_document(self, document: RagDocument) -> None:
        if not document.text.strip():
            raise ValueError("Each document must have text")
        if not document.agent_id.strip():
            raise ValueError("Each document must have agentId")
        if not document.embedding_name.strip():
            raise ValueError("Each document must have embeddingName")

    def _enrich_chunk(self, text: str, extra_fields: dict[str, Any], part: str) -> str:
        header = json.dumps(extra_fields, ensure_ascii=False, sort_keys=True)
        return f"metadata: {header}\npart: {part}\ntexto: {text}"

    def _context_from_docs(self, docs: list[RagSearchResult]) -> str:
        blocks = []
        for index, doc in enumerate(docs, start=1):
            extra_fields = json.dumps(doc.extra_fields, ensure_ascii=False, sort_keys=True)
            blocks.append(
                "\n".join(
                    [
                        f"[doc {index} | score={doc.score:.4f}]",
                        f"Embedding name: {doc.embedding_name}",
                        f"Text of doc: {doc.text}",
                        f"Extra fields: {extra_fields}",
                    ]
                )
            )
        return "\n\n".join(blocks)

    def _dedupe_key(self, agent_id: str, text: str) -> str:
        return hashlib.sha256(f"{agent_id}:{text}".encode("utf-8")).hexdigest()

    def _embedding_id(self, document: RagDocument) -> str:
        value = f"{document.agent_id}:{document.embedding_name}:{document.text}"
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]


def rag_search_options_from_dict(params: dict[str, Any]) -> RagSearchOptions:
    return RagSearchOptions(
        k=int(params.get("k", 15)),
        dense_weight=float(params.get("denseWeight", 0.7)),
        sparse_weight=float(params.get("sparseWeight", 0.3)),
        use_hybrid=_as_bool(params.get("useHybrid", True)),
        relevance_boost=float(params.get("relevanceBoost", 1.5)),
        candidate_multiplier=int(params.get("candidateMultiplier", 4)),
        candidate_top_k=(
            int(params["candidateTopK"]) if params.get("candidateTopK") is not None else None
        ),
        dense_ef_search=int(params.get("denseEfSearch", 128)),
        sparse_drop_ratio_search=float(params.get("sparseDropRatioSearch", 0.2)),
        fusion_strategy=params.get("fusionStrategy", "rrf"),
        rrf_k=int(params.get("rrfK", 60)),
        max_chunks_per_document=(
            int(params["maxChunksPerDocument"])
            if params.get("maxChunksPerDocument") is not None
            else None
        ),
    )


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "nao", "off"}
    return bool(value)


def rag_result_to_dict(result: RagSearchResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "score": result.score,
        "text": result.text,
        "agentId": result.agent_id,
        "embeddingName": result.embedding_name,
        "embeddingId": result.embedding_id,
        "extraFields": result.extra_fields,
        "denseScore": result.dense_score,
        "sparseScore": result.sparse_score,
    }
