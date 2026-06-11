from typing import Any

from app.domain.entities.llm import ChatRequest, ChatResponse, ProviderName


class ClaudeLlmAdapter:
    provider: ProviderName = "claude"

    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key

    def generate(self, request: ChatRequest) -> ChatResponse:
        if not self._api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")

        from anthropic import Anthropic

        client = Anthropic(api_key=self._api_key)
        messages = [
            {"role": message.role, "content": message.content}
            for message in request.messages
            if message.role != "system"
        ]
        if not messages:
            raise ValueError("At least one user or assistant message is required")

        payload: dict[str, Any] = {
            "model": request.model,
            "max_tokens": request.max_tokens or 1024,
            "messages": messages,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        system_prompt = self._system_prompt(request)
        if system_prompt:
            payload["system"] = system_prompt

        response = client.messages.create(**payload)

        return ChatResponse(
            provider=self.provider,
            model=request.model,
            text=self._extract_text(response),
            usage=self._usage(response),
            raw={
                "id": getattr(response, "id", None),
                "stopReason": getattr(response, "stop_reason", None),
            },
        )

    def _system_prompt(self, request: ChatRequest) -> str | None:
        parts = []
        system_from_messages = [
            message.content for message in request.messages if message.role == "system"
        ]
        parts.extend(system_from_messages)
        if request.system_prompt:
            parts.append(request.system_prompt)
        if request.context:
            parts.append(
                "Use o contexto abaixo quando ele for relevante. "
                "Se o contexto nao responder a pergunta, diga isso com clareza.\n\n"
                f"{request.context}"
            )
        return "\n\n".join(part.strip() for part in parts if part and part.strip()) or None

    def _extract_text(self, response: Any) -> str:
        blocks = []
        for block in getattr(response, "content", []) or []:
            text = getattr(block, "text", None)
            if text:
                blocks.append(text)
        return "\n".join(blocks).strip()

    def _usage(self, response: Any) -> dict[str, Any]:
        usage = getattr(response, "usage", None)
        if usage is None:
            return {}
        return {
            "inputTokens": getattr(usage, "input_tokens", None),
            "outputTokens": getattr(usage, "output_tokens", None),
        }
