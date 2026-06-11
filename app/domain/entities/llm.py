from dataclasses import dataclass, field
from typing import Any, Literal

ProviderName = Literal["openai", "claude"]
MessageRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: MessageRole
    content: str


@dataclass(frozen=True)
class ChatRequest:
    provider: ProviderName
    model: str
    messages: list[ChatMessage]
    system_prompt: str | None = None
    context: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChatResponse:
    provider: ProviderName
    model: str
    text: str
    usage: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
