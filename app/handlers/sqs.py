import json
from typing import Any

from app.application.container import get_process_conversation_use_case
from app.infrastructure.conversation.payload_mapper import conversation_from_payload


def _message_attribute(record: dict[str, Any], name: str) -> str | None:
    attribute = record.get("messageAttributes", {}).get(name)
    if not isinstance(attribute, dict):
        return None
    return attribute.get("stringValue") or attribute.get("StringValue")


def handle_sqs_event(event: dict[str, Any], context: Any) -> dict[str, Any]:
    records = event.get("Records") or []
    batch_item_failures: list[dict[str, str]] = []

    for record in records:
        message_id = record.get("messageId", "")
        try:
            process_record(record)
        except Exception as exc:
            print(f"Error processing SQS record {message_id}: {exc}")
            if message_id:
                batch_item_failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": batch_item_failures}


def handle_direct_event(event: dict[str, Any], context: Any) -> dict[str, Any]:
    message_payload = {
        **event,
        "convId": event.get("convId") or event.get("conversationId"),
        "requestId": event.get("requestId") or event.get("conversationId"),
    }
    fake_record = {
        "messageId": f"direct-{message_payload.get('requestId', 'unknown')}",
        "body": json.dumps(message_payload, default=str),
        "messageAttributes": {
            "MessageType": {
                "stringValue": "nlp-conversation",
            }
        },
    }

    process_record(fake_record)
    return {"statusCode": 200, "body": json.dumps({"ok": True})}


def process_record(record: dict[str, Any]) -> None:
    message_type = _message_attribute(record, "MessageType")

    if message_type == "nlp-conversation":
        process_conversation_record(record)
        return

    print(f"Unknown SQS message type: {message_type}")


def process_conversation_record(record: dict[str, Any]) -> None:
    body = json.loads(record.get("body") or "{}")
    result = get_process_conversation_use_case().execute(conversation_from_payload(body))
    print("Processing conversation", result.__dict__)

    # Replace this with your NLP/orchestration logic.
    # Keep this function idempotent because SQS may retry the same message.
