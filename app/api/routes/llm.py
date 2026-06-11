from typing import Any, Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.application.container import get_chat_use_case
from app.core.config import get_settings
from app.domain.entities.llm import ChatMessage

router = APIRouter(prefix="/api/llm", tags=["llm"])


class ApiChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = "user"
    content: str


class ChatRequestBody(BaseModel):
    provider: Literal["openai", "claude"]
    model: str | None = None
    text: str | None = None
    messages: list[ApiChatMessage] | None = None
    system_prompt: str | None = Field(default=None, alias="systemPrompt")
    context: str | None = None
    temperature: float | None = None
    max_tokens: int | None = Field(default=None, alias="maxTokens")
    reasoning_effort: str | None = Field(default=None, alias="reasoningEffort")
    verbosity: str | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


@router.get("/models")
def models() -> dict[str, Any]:
    settings = get_settings()
    return {
        "providers": {
            "openai": {
                "defaultModel": settings.openai_default_model,
                "embeddingModel": settings.openai_embedding_model,
            },
            "claude": {
                "defaultModel": settings.anthropic_default_model,
            },
        }
    }


@router.post("/chat")
def chat(payload: ChatRequestBody) -> dict[str, Any]:
    messages = _messages_from_payload(payload)
    try:
        response = get_chat_use_case().execute(
            provider=payload.provider,
            model=payload.model,
            messages=messages,
            system_prompt=payload.system_prompt,
            context=payload.context,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            extra={
                "reasoningEffort": payload.reasoning_effort,
                "verbosity": payload.verbosity,
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {
        "provider": response.provider,
        "model": response.model,
        "text": response.text,
        "usage": response.usage,
        "raw": response.raw,
    }


def _messages_from_payload(payload: ChatRequestBody) -> list[ChatMessage]:
    if payload.messages:
        return [
            ChatMessage(role=message.role, content=message.content)
            for message in payload.messages
        ]
    if payload.text:
        return [ChatMessage(role="user", content=payload.text)]
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Send either text or messages",
    )
