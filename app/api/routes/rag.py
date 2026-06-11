from typing import Any, Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.application.container import get_rag_use_case
from app.application.use_cases.rag import rag_result_to_dict, rag_search_options_from_dict
from app.domain.entities.rag import RagDocument

router = APIRouter(prefix="/api/rag", tags=["rag"])


class CreateCollectionRequest(BaseModel):
    collection_name: str | None = Field(default=None, alias="collectionName")
    embedding_dim: int | None = Field(default=None, alias="embeddingDim")

    model_config = ConfigDict(populate_by_name=True)


class CreateIndexRequest(BaseModel):
    collection_name: str | None = Field(default=None, alias="collectionName")

    model_config = ConfigDict(populate_by_name=True)


class EmbeddingCreateRequest(BaseModel):
    text: str


class RagDocumentIn(BaseModel):
    text: str
    agent_id: str = Field(alias="agentId")
    embedding_name: str = Field(alias="embeddingName")
    embedding_id: str | None = Field(default=None, alias="embeddingId")
    extra_fields: dict[str, Any] | str | None = Field(default=None, alias="extraFields")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class AddDocumentsRequest(BaseModel):
    collection_name: str | None = Field(default=None, alias="collectionName")
    documents: list[RagDocumentIn]
    chunk_size: int = Field(default=512, alias="chunkSize")
    chunk_overlap: int = Field(default=70, alias="chunkOverlap")
    batch_size: int = Field(default=100, alias="batchSize")
    deduplicate: bool = False
    no_split: bool = Field(default=False, alias="noSplit")
    no_header: bool = Field(default=False, alias="noHeader")

    model_config = ConfigDict(populate_by_name=True)


class SearchHybridRequest(BaseModel):
    query: str
    agent_id: str = Field(alias="agentId")
    collection_name: str | None = Field(default=None, alias="collectionName")
    extra_fields: dict[str, Any] | None = Field(default=None, alias="extraFields")
    k: int = 15
    dense_weight: float = Field(default=0.7, alias="denseWeight")
    sparse_weight: float = Field(default=0.3, alias="sparseWeight")
    use_hybrid: bool = Field(default=True, alias="useHybrid")
    relevance_boost: float = Field(default=1.5, alias="relevanceBoost")
    candidate_multiplier: int = Field(default=4, alias="candidateMultiplier")
    candidate_top_k: int | None = Field(default=None, alias="candidateTopK")
    dense_ef_search: int = Field(default=128, alias="denseEfSearch")
    sparse_drop_ratio_search: float = Field(default=0.2, alias="sparseDropRatioSearch")
    fusion_strategy: Literal["rrf", "weighted_score"] = Field(default="rrf", alias="fusionStrategy")
    rrf_k: int = Field(default=60, alias="rrfK")
    max_chunks_per_document: int | None = Field(default=None, alias="maxChunksPerDocument")

    model_config = ConfigDict(populate_by_name=True)


class ChatLlmRagRequest(BaseModel):
    text: str
    agent_id: str = Field(alias="agentId")
    provider: Literal["openai", "claude"]
    model: str | None = None
    collection_name: str | None = Field(default=None, alias="collectionName")
    system_prompt: str | None = Field(default=None, alias="systemPrompt")
    params: dict[str, Any] = Field(default_factory=dict)
    extra_fields: dict[str, Any] | None = Field(default=None, alias="extraFields")
    temperature: float | None = None
    max_tokens: int | None = Field(default=None, alias="maxTokens")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


@router.post("/create-collection")
def create_collection(payload: CreateCollectionRequest) -> dict[str, Any]:
    try:
        return get_rag_use_case().create_collection(
            collection_name=payload.collection_name,
            embedding_dim=payload.embedding_dim,
        )
    except (ValueError, RuntimeError) as exc:
        raise _http_error(exc) from exc


@router.post("/create-index")
def create_index(payload: CreateIndexRequest) -> dict[str, Any]:
    try:
        return get_rag_use_case().create_index(collection_name=payload.collection_name)
    except (ValueError, RuntimeError) as exc:
        raise _http_error(exc) from exc


@router.post("/embedding-create")
def embedding_create(payload: EmbeddingCreateRequest) -> dict[str, Any]:
    try:
        return get_rag_use_case().embedding_create(payload.text)
    except (ValueError, RuntimeError) as exc:
        raise _http_error(exc) from exc


@router.post("/add-documents")
def add_documents(payload: AddDocumentsRequest) -> dict[str, Any]:
    documents = [
        RagDocument(
            text=document.text,
            agent_id=document.agent_id,
            embedding_name=document.embedding_name,
            embedding_id=document.embedding_id,
            extra_fields=document.extra_fields or {},
        )
        for document in payload.documents
    ]
    try:
        return get_rag_use_case().add_documents(
            documents=documents,
            collection_name=payload.collection_name,
            chunk_size=payload.chunk_size,
            chunk_overlap=payload.chunk_overlap,
            batch_size=payload.batch_size,
            deduplicate=payload.deduplicate,
            no_split=payload.no_split,
            no_header=payload.no_header,
        )
    except (ValueError, RuntimeError) as exc:
        raise _http_error(exc) from exc


@router.post("/search-hybrid")
def search_hybrid(payload: SearchHybridRequest) -> dict[str, Any]:
    params = payload.model_dump(by_alias=True)
    try:
        results = get_rag_use_case().search_hybrid(
            query=payload.query,
            agent_id=payload.agent_id,
            collection_name=payload.collection_name,
            options=rag_search_options_from_dict(params),
            extra_filters=payload.extra_fields,
        )
        return {"results": [rag_result_to_dict(result) for result in results]}
    except (ValueError, RuntimeError) as exc:
        raise _http_error(exc) from exc


@router.post("/chat-llm-rag")
def chat_llm_rag(payload: ChatLlmRagRequest) -> dict[str, Any]:
    try:
        return get_rag_use_case().chat(
            text=payload.text,
            agent_id=payload.agent_id,
            provider=payload.provider,
            model=payload.model,
            collection_name=payload.collection_name,
            system_prompt=payload.system_prompt,
            params=payload.params,
            extra_filters=payload.extra_fields,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        )
    except (ValueError, RuntimeError) as exc:
        raise _http_error(exc) from exc


def _http_error(exc: Exception) -> HTTPException:
    code = (
        status.HTTP_400_BAD_REQUEST
        if isinstance(exc, ValueError)
        else status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    return HTTPException(status_code=code, detail=str(exc))
