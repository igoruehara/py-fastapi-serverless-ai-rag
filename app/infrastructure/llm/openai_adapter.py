from typing import Any

from app.domain.entities.llm import ChatRequest, ChatResponse, ProviderName


class OpenAiLlmAdapter:
    provider: ProviderName = "openai"

    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key

    def generate(self, request: ChatRequest) -> ChatResponse:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        from openai import OpenAI

        client = OpenAI(api_key=self._api_key)
        input_messages = [
            {"role": message.role, "content": message.content}
            for message in request.messages
            if message.role != "system"
        ]
        if not input_messages:
            raise ValueError("At least one user or assistant message is required")

        payload: dict[str, Any] = {
            "model": request.model,
            "input": input_messages,
        }
        instructions = self._instructions(request)
        if instructions:
            payload["instructions"] = instructions
        if request.max_tokens is not None:
            payload["max_output_tokens"] = request.max_tokens
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.extra.get("reasoningEffort"):
            payload["reasoning"] = {"effort": request.extra["reasoningEffort"]}
        if request.extra.get("verbosity"):
            payload["text"] = {"verbosity": request.extra["verbosity"]}

        response = client.responses.create(**payload)
        return ChatResponse(
            provider=self.provider,
            model=request.model,
            text=self._extract_text(response),
            usage=self._usage(response),
            raw={"id": getattr(response, "id", None), "status": getattr(response, "status", None)},
        )

    def _instructions(self, request: ChatRequest) -> str | None:
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
        output_text = getattr(response, "output_text", None)
        if output_text:
            return str(output_text).strip()

        blocks: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
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
            "totalTokens": getattr(usage, "total_tokens", None),
        }


class OpenAiEmbeddingAdapter:
    def __init__(self, api_key: str | None, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def embed_text(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        if not texts:
            return []

        from openai import OpenAI

        client = OpenAI(api_key=self._api_key)
        response = client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]
