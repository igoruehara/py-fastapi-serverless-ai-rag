from typing import Protocol


class EmbeddingPort(Protocol):
    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
