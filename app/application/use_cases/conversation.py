from dataclasses import dataclass

from app.domain.entities.conversation import ConversationMessage
from app.domain.ports.conversation_queue import ConversationQueuePort


@dataclass(frozen=True)
class EnqueueConversationResult:
    queued: bool
    message_id: str


@dataclass(frozen=True)
class ProcessConversationResult:
    processed: bool
    request_id: str
    conversation_id: str
    agent_id: str
    channel: str | None


class EnqueueConversationUseCase:
    def __init__(self, queue: ConversationQueuePort) -> None:
        self._queue = queue

    def execute(self, message: ConversationMessage) -> EnqueueConversationResult:
        self._validate(message)
        message_id = self._queue.enqueue(message)
        return EnqueueConversationResult(queued=True, message_id=message_id)

    def _validate(self, message: ConversationMessage) -> None:
        if not message.message.strip():
            raise ValueError("message is required")
        if not message.conversation_id.strip():
            raise ValueError("conversationId is required")
        if not message.agent_id.strip():
            raise ValueError("agentId is required")
        if not message.request_id.strip():
            raise ValueError("requestId is required")


class ProcessConversationUseCase:
    def execute(self, message: ConversationMessage) -> ProcessConversationResult:
        return ProcessConversationResult(
            processed=True,
            request_id=message.request_id,
            conversation_id=message.conversation_id,
            agent_id=message.agent_id,
            channel=message.channel,
        )
