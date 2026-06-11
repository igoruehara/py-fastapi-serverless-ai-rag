import json
from typing import Any

from app.domain.entities.conversation import ConversationMessage


class SqsConversationQueueAdapter:
    def __init__(self, queue_url: str | None, aws_region: str) -> None:
        self._queue_url = queue_url
        self._aws_region = aws_region
        self._client: Any | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            import boto3

            self._client = boto3.client("sqs", region_name=self._aws_region)
        return self._client

    def enqueue(self, message: ConversationMessage) -> str:
        if not self._queue_url:
            raise RuntimeError("NLP_CONVERSATION_QUEUE_URL is not configured")

        result = self.client.send_message(
            QueueUrl=self._queue_url,
            MessageBody=json.dumps(message.to_payload(), default=str),
            MessageAttributes={
                "MessageType": {
                    "DataType": "String",
                    "StringValue": "nlp-conversation",
                },
                "AgentId": {
                    "DataType": "String",
                    "StringValue": message.agent_id,
                },
                "ConversationId": {
                    "DataType": "String",
                    "StringValue": message.conversation_id,
                },
            },
        )
        return result["MessageId"]
