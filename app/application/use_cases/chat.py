from app.domain.entities.llm import ChatMessage, ChatRequest, ChatResponse, ProviderName
from app.domain.ports.llm import LlmProviderPort


class ChatUseCase:
    def __init__(
        self,
        providers: dict[str, LlmProviderPort],
        default_models: dict[str, str | None] | None = None,
    ) -> None:
        self._providers = providers
        self._default_models = default_models or {}

    def execute(
        self,
        provider: ProviderName,
        model: str | None,
        messages: list[ChatMessage],
        system_prompt: str | None = None,
        context: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        extra: dict | None = None,
    ) -> ChatResponse:
        provider_key = provider.lower()
        adapter = self._providers.get(provider_key)
        if adapter is None:
            available = ", ".join(sorted(self._providers))
            raise ValueError(f"Provider '{provider}' is not supported. Use one of: {available}")

        selected_model = (model or self._default_models.get(provider_key) or "").strip()
        if not selected_model:
            raise ValueError(f"Model is required for provider '{provider_key}'")

        clean_messages = [
            ChatMessage(role=message.role, content=message.content.strip())
            for message in messages
            if message.content and message.content.strip()
        ]
        if not clean_messages:
            raise ValueError("At least one message with content is required")

        request = ChatRequest(
            provider=provider_key,  # type: ignore[arg-type]
            model=selected_model,
            messages=clean_messages,
            system_prompt=system_prompt,
            context=context,
            temperature=temperature,
            max_tokens=max_tokens,
            extra=extra or {},
        )
        return adapter.generate(request)
