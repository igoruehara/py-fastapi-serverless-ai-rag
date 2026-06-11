from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from app.domain.entities.rag import RagChunk, RagSearchOptions, RagSearchResult


class MilvusRagVectorStore:
    def __init__(
        self,
        uri: str | None,
        token: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self._uri = uri
        self._token = token
        self._username = username
        self._password = password
        self._client: Any | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            if not self._uri:
                raise RuntimeError("MILVUS_URI is not configured")

            from pymilvus import MilvusClient

            kwargs: dict[str, Any] = {}
            if self._token:
                kwargs["token"] = self._token
            elif self._username and self._password:
                kwargs["user"] = self._username
                kwargs["password"] = self._password
            self._client = MilvusClient(uri=self._uri, **kwargs)
        return self._client

    def create_collection(self, collection_name: str, embedding_dim: int) -> dict[str, Any]:
        from pymilvus import DataType, Function, FunctionType

        if self.client.has_collection(collection_name=collection_name):
            return {"collectionName": collection_name, "created": False}

        schema = self.client.create_schema(auto_id=True, enable_dynamic_field=False)
        schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, auto_id=True)
        schema.add_field(
            field_name="embeddingName",
            datatype=DataType.VARCHAR,
            max_length=1000,
            enable_analyzer=True,
        )
        schema.add_field(
            field_name="agentId",
            datatype=DataType.VARCHAR,
            max_length=500,
            enable_analyzer=True,
        )
        schema.add_field(
            field_name="embeddingId",
            datatype=DataType.VARCHAR,
            max_length=500,
            enable_analyzer=True,
        )
        schema.add_field(field_name="extraFields", datatype=DataType.JSON)
        schema.add_field(
            field_name="text",
            datatype=DataType.VARCHAR,
            max_length=10000,
            enable_analyzer=True,
        )
        schema.add_field(field_name="dense", datatype=DataType.FLOAT_VECTOR, dim=embedding_dim)
        schema.add_field(field_name="sparse", datatype=DataType.SPARSE_FLOAT_VECTOR)
        schema.add_function(
            Function(
                name="text_bm25_emb",
                input_field_names=["text"],
                output_field_names=["sparse"],
                function_type=FunctionType.BM25,
            )
        )

        self.client.create_collection(collection_name=collection_name, schema=schema)
        return {"collectionName": collection_name, "created": True}

    def create_index(self, collection_name: str) -> dict[str, Any]:
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="dense",
            index_name="dense_hnsw_index",
            index_type="HNSW",
            metric_type="COSINE",
            params={"M": 16, "efConstruction": 200},
        )
        index_params.add_index(
            field_name="sparse",
            index_name="sparse_bm25_index",
            index_type="SPARSE_INVERTED_INDEX",
            metric_type="BM25",
            params={"drop_ratio_build": 0.2, "bm25_k1": 1.2, "bm25_b": 0.75},
        )
        self.client.create_index(collection_name=collection_name, index_params=index_params)
        try:
            self.client.load_collection(collection_name=collection_name)
        except Exception:
            pass
        return {"collectionName": collection_name, "indexed": True}

    def add_chunks(self, collection_name: str, chunks: list[RagChunk]) -> dict[str, Any]:
        if not chunks:
            return {"inserted": 0}

        rows = [
            {
                "embeddingName": chunk.embedding_name,
                "agentId": chunk.agent_id,
                "embeddingId": chunk.embedding_id,
                "extraFields": chunk.extra_fields,
                "text": chunk.text,
                "dense": chunk.dense_embedding,
            }
            for chunk in chunks
        ]
        result = self.client.insert(collection_name=collection_name, data=rows)
        self._flush(collection_name)
        return {"inserted": len(rows), "result": result}

    def search_hybrid(
        self,
        collection_name: str,
        query: str,
        query_embedding: list[float],
        agent_id: str,
        options: RagSearchOptions,
        extra_filters: dict[str, Any] | None = None,
    ) -> list[RagSearchResult]:
        candidate_top_k = options.candidate_top_k or max(
            options.k,
            options.k * max(options.candidate_multiplier, 1),
        )
        expr = self._filter_expression(agent_id=agent_id, extra_filters=extra_filters or {})
        dense_hits = self._search_dense(
            collection_name=collection_name,
            query_embedding=query_embedding,
            expr=expr,
            limit=candidate_top_k,
            ef_search=options.dense_ef_search,
        )
        sparse_hits: list[_Hit] = []
        if options.use_hybrid and options.sparse_weight > 0:
            sparse_hits = self._search_sparse(
                collection_name=collection_name,
                query=query,
                expr=expr,
                limit=candidate_top_k,
                drop_ratio=options.sparse_drop_ratio_search,
            )

        fused = self._fuse_hits(dense_hits=dense_hits, sparse_hits=sparse_hits, options=options)
        diversified = self._diversify(
            fused,
            max_chunks_per_document=options.max_chunks_per_document,
        )
        return diversified[: options.k]

    def _search_dense(
        self,
        collection_name: str,
        query_embedding: list[float],
        expr: str,
        limit: int,
        ef_search: int,
    ) -> list["_Hit"]:
        result = self.client.search(
            collection_name=collection_name,
            data=[query_embedding],
            anns_field="dense",
            filter=expr,
            limit=limit,
            output_fields=["text", "agentId", "embeddingName", "embeddingId", "extraFields"],
            search_params={"metric_type": "COSINE", "params": {"ef": ef_search}},
        )
        return self._flatten_hits(result)

    def _search_sparse(
        self,
        collection_name: str,
        query: str,
        expr: str,
        limit: int,
        drop_ratio: float,
    ) -> list["_Hit"]:
        try:
            result = self.client.search(
                collection_name=collection_name,
                data=[query],
                anns_field="sparse",
                filter=expr,
                limit=limit,
                output_fields=["text", "agentId", "embeddingName", "embeddingId", "extraFields"],
                search_params={"metric_type": "BM25", "params": {"drop_ratio_search": drop_ratio}},
            )
            return self._flatten_hits(result)
        except Exception:
            return []

    def _fuse_hits(
        self,
        dense_hits: list["_Hit"],
        sparse_hits: list["_Hit"],
        options: RagSearchOptions,
    ) -> list[RagSearchResult]:
        dense_by_id = {hit.id: hit for hit in dense_hits}
        sparse_by_id = {hit.id: hit for hit in sparse_hits}
        ids = list(dict.fromkeys([hit.id for hit in dense_hits] + [hit.id for hit in sparse_hits]))

        dense_norm = _normalize_scores(dense_hits)
        sparse_norm = _normalize_scores(sparse_hits)
        dense_ranks = {hit.id: index for index, hit in enumerate(dense_hits, start=1)}
        sparse_ranks = {hit.id: index for index, hit in enumerate(sparse_hits, start=1)}

        results: list[RagSearchResult] = []
        for hit_id in ids:
            hit = dense_by_id.get(hit_id) or sparse_by_id[hit_id]
            if options.fusion_strategy == "weighted_score":
                score = (
                    options.dense_weight * dense_norm.get(hit_id, 0.0)
                    + options.sparse_weight * sparse_norm.get(hit_id, 0.0)
                )
            else:
                dense_rank_score = (
                    1 / (options.rrf_k + dense_ranks[hit_id]) if hit_id in dense_ranks else 0.0
                )
                sparse_rank_score = (
                    1 / (options.rrf_k + sparse_ranks[hit_id]) if hit_id in sparse_ranks else 0.0
                )
                score = (
                    options.dense_weight * dense_rank_score
                    + options.sparse_weight * sparse_rank_score
                )

            extra_fields = hit.extra_fields
            if extra_fields.get("relevante") is True:
                score *= options.relevance_boost

            results.append(
                RagSearchResult(
                    id=hit_id,
                    score=score,
                    text=hit.text,
                    agent_id=hit.agent_id,
                    embedding_name=hit.embedding_name,
                    embedding_id=hit.embedding_id,
                    extra_fields=extra_fields,
                    dense_score=dense_by_id.get(hit_id).score if hit_id in dense_by_id else None,
                    sparse_score=sparse_by_id.get(hit_id).score if hit_id in sparse_by_id else None,
                )
            )

        return sorted(results, key=lambda item: item.score, reverse=True)

    def _diversify(
        self,
        results: list[RagSearchResult],
        max_chunks_per_document: int | None,
    ) -> list[RagSearchResult]:
        if not max_chunks_per_document or max_chunks_per_document <= 0:
            return results

        counts: dict[str, int] = defaultdict(int)
        diversified = []
        for result in results:
            document_key = result.embedding_id or result.embedding_name or result.id
            if counts[document_key] >= max_chunks_per_document:
                continue
            counts[document_key] += 1
            diversified.append(result)
        return diversified

    def _flatten_hits(self, result: Any) -> list["_Hit"]:
        rows = result[0] if result and isinstance(result, list) else []
        hits = [self._hit_from_row(row) for row in rows]
        return sorted(
            [hit for hit in hits if hit is not None],
            key=lambda hit: hit.score,
            reverse=True,
        )

    def _hit_from_row(self, row: Any) -> "_Hit | None":
        if isinstance(row, dict):
            entity = row.get("entity") or row
            row_id = row.get("id") or row.get("pk") or entity.get("id")
            score = row.get("distance", row.get("score", 0.0))
        else:
            entity = getattr(row, "entity", None) or {}
            row_id = getattr(row, "id", None) or getattr(row, "pk", None)
            score = getattr(row, "distance", getattr(row, "score", 0.0))

        if row_id is None:
            return None
        if not isinstance(entity, dict):
            entity = dict(entity)

        return _Hit(
            id=str(row_id),
            score=float(score or 0.0),
            text=str(entity.get("text") or ""),
            agent_id=str(entity.get("agentId") or ""),
            embedding_name=str(entity.get("embeddingName") or ""),
            embedding_id=str(entity.get("embeddingId") or ""),
            extra_fields=entity.get("extraFields") or {},
        )

    def _filter_expression(self, agent_id: str, extra_filters: dict[str, Any]) -> str:
        expressions = [f'agentId == "{_escape_expr(agent_id)}"']
        for key, value in extra_filters.items():
            if value is None:
                continue
            safe_key = _escape_json_key(str(key))
            expressions.append(f'extraFields["{safe_key}"] == {_literal(value)}')
        return " and ".join(expressions)

    def _flush(self, collection_name: str) -> None:
        try:
            self.client.flush(collection_name=collection_name)
        except TypeError:
            self.client.flush(collection_names=[collection_name])


class _Hit:
    def __init__(
        self,
        id: str,
        score: float,
        text: str,
        agent_id: str,
        embedding_name: str,
        embedding_id: str,
        extra_fields: dict[str, Any],
    ) -> None:
        self.id = id
        self.score = score
        self.text = text
        self.agent_id = agent_id
        self.embedding_name = embedding_name
        self.embedding_id = embedding_id
        self.extra_fields = extra_fields


def _normalize_scores(hits: list[_Hit]) -> dict[str, float]:
    if not hits:
        return {}
    values = [hit.score for hit in hits]
    min_value = min(values)
    max_value = max(values)
    if max_value == min_value:
        return {hit.id: 1.0 for hit in hits}
    return {hit.id: (hit.score - min_value) / (max_value - min_value) for hit in hits}


def _literal(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def _escape_expr(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _escape_json_key(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
