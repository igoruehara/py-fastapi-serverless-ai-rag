from typing import Any, Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.application.container import get_enqueue_conversation_use_case
from app.domain.entities.conversation import ConversationMessage

router = APIRouter(prefix="/api", tags=["conversation"])


class ConversationRequest(BaseModel):
    message: str
    conversation_id: str = Field(alias="conversationId")
    context: dict[str, Any] = Field(default_factory=dict)
    agent_id: str = Field(alias="agentId")
    request_id: str = Field(alias="requestId")
    timestamp: int
    channel: Literal["whatsapp", "webchat"] | None = None
    conv_id: str | None = Field(default=None, alias="convId")
    from_: str | None = Field(default=None, alias="from")

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    def to_domain(self) -> ConversationMessage:
        return ConversationMessage(
            message=self.message,
            conversation_id=self.conversation_id,
            context=self.context,
            agent_id=self.agent_id,
            request_id=self.request_id,
            timestamp=self.timestamp,
            channel=self.channel,
            conv_id=self.conv_id,
            from_=self.from_,
            extra=self.model_extra or {},
        )


@router.post("/conversation", status_code=status.HTTP_202_ACCEPTED)
def enqueue_conversation(payload: ConversationRequest) -> dict[str, str | bool]:
    try:
        result = get_enqueue_conversation_use_case().execute(payload.to_domain())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return {"queued": result.queued, "messageId": result.message_id}
