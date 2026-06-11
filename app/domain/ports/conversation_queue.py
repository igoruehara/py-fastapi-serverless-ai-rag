from typing import Protocol

from app.domain.entities.conversation import ConversationMessage


class ConversationQueuePort(Protocol):
    def enqueue(self, message: ConversationMessage) -> str:
        raise NotImplementedError
