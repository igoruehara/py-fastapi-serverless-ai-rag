from functools import lru_cache

from app.application.use_cases.conversation import (
    EnqueueConversationUseCase,
    ProcessConversationUseCase,
)
from app.application.use_cases.chat import ChatUseCase
from app.application.use_cases.rag import RagUseCase
from app.core.config import Settings, get_settings
from app.infrastructure.conversation.sqs_queue import SqsConversationQueueAdapter
from app.infrastructure.llm.anthropic_adapter import ClaudeLlmAdapter
from app.infrastructure.llm.openai_adapter import OpenAiEmbeddingAdapter, OpenAiLlmAdapter
from app.infrastructure.rag.milvus_store import MilvusRagVectorStore


def _clean_model(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


@lru_cache(maxsize=1)
def get_chat_use_case() -> ChatUseCase:
    settings = get_settings()
    return _build_chat_use_case(settings)


@lru_cache(maxsize=1)
def get_rag_use_case() -> RagUseCase:
    settings = get_settings()
    chat_use_case = _build_chat_use_case(settings)
    vector_store = MilvusRagVectorStore(
        uri=settings.milvus_uri,
        token=settings.milvus_token,
        username=settings.milvus_username,
        password=settings.milvus_password,
    )
    embeddings = OpenAiEmbeddingAdapter(
        api_key=settings.openai_api_key,
        model=settings.openai_embedding_model,
    )
    return RagUseCase(
        vector_store=vector_store,
        embeddings=embeddings,
        chat_use_case=chat_use_case,
        default_collection=settings.milvus_collection_name,
        embedding_dim=settings.milvus_embedding_dim,
    )


@lru_cache(maxsize=1)
def get_enqueue_conversation_use_case() -> EnqueueConversationUseCase:
    settings = get_settings()
    queue = SqsConversationQueueAdapter(
        queue_url=settings.nlp_conversation_queue_url,
        aws_region=settings.aws_region,
    )
    return EnqueueConversationUseCase(queue=queue)


@lru_cache(maxsize=1)
def get_process_conversation_use_case() -> ProcessConversationUseCase:
    return ProcessConversationUseCase()


def _build_chat_use_case(settings: Settings) -> ChatUseCase:
    return ChatUseCase(
        providers={
            "openai": OpenAiLlmAdapter(api_key=settings.openai_api_key),
            "claude": ClaudeLlmAdapter(api_key=settings.anthropic_api_key),
        },
        default_models={
            "openai": _clean_model(settings.openai_default_model),
            "claude": _clean_model(settings.anthropic_default_model),
        },
    )
