from __future__ import annotations

import time
from typing import Any

from app.domain.entities.conversation import ConversationMessage

_KNOWN_KEYS = {
    "message",
    "conversationId",
    "conversation_id",
    "context",
    "agentId",
    "agent_id",
    "requestId",
    "request_id",
    "timestamp",
    "channel",
    "convId",
    "conv_id",
    "from",
    "from_",
}


def conversation_from_payload(payload: dict[str, Any]) -> ConversationMessage:
    context = payload.get("context")
    extra = {key: value for key, value in payload.items() if key not in _KNOWN_KEYS}
    return ConversationMessage(
        message=str(payload.get("message") or ""),
        conversation_id=str(payload.get("conversationId") or payload.get("conversation_id") or ""),
        agent_id=str(payload.get("agentId") or payload.get("agent_id") or ""),
        request_id=str(payload.get("requestId") or payload.get("request_id") or ""),
        timestamp=_timestamp(payload.get("timestamp")),
        context=context if isinstance(context, dict) else {},
        channel=payload.get("channel"),
        conv_id=payload.get("convId") or payload.get("conv_id"),
        from_=payload.get("from") or payload.get("from_"),
        extra=extra,
    )


def _timestamp(value: Any) -> int:
    if value is None or value == "":
        return int(time.time() * 1000)
    return int(value)
