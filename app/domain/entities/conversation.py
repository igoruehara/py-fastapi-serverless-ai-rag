from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ConversationMessage:
    message: str
    conversation_id: str
    agent_id: str
    request_id: str
    timestamp: int
    context: dict[str, Any] = field(default_factory=dict)
    channel: str | None = None
    conv_id: str | None = None
    from_: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            **self.extra,
            "message": self.message,
            "conversationId": self.conversation_id,
            "context": self.context,
            "agentId": self.agent_id,
            "requestId": self.request_id,
            "timestamp": self.timestamp,
        }
        if self.channel is not None:
            payload["channel"] = self.channel
        if self.conv_id is not None:
            payload["convId"] = self.conv_id
        if self.from_ is not None:
            payload["from"] = self.from_
        return payload
