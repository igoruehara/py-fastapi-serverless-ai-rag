from typing import Protocol

from app.domain.entities.llm import ChatRequest, ChatResponse, ProviderName


class LlmProviderPort(Protocol):
    provider: ProviderName

    def generate(self, request: ChatRequest) -> ChatResponse:
        raise NotImplementedError
