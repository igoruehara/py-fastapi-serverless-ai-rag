import json
from typing import Any, Literal

from mangum import Mangum

from app.core.logging import sanitize_event_for_log
from app.handlers.sqs import handle_direct_event, handle_sqs_event
from app.handlers.websocket import (
    handle_ws_connect,
    handle_ws_default,
    handle_ws_disconnect,
)
from app.main import app

asgi_handler = Mangum(app, lifespan="off")

EventType = Literal[
    "http",
    "sqs",
    "sns",
    "scheduled",
    "warmup",
    "direct",
    "wsConnect",
    "wsDisconnect",
    "wsDefault",
    "unknown",
]


def _delete_header(headers: dict[str, Any] | None, name: str) -> None:
    if not isinstance(headers, dict):
        return
    wanted = name.lower()
    for key in list(headers.keys()):
        if key.lower() == wanted:
            del headers[key]


def _set_single_header(response: dict[str, Any], name: str, value: str) -> None:
    response.setdefault("headers", {})
    _delete_header(response.get("headers"), name)
    _delete_header(response.get("multiValueHeaders"), name)
    response["headers"][name] = value


def normalize_cors_response(response: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(response, dict):
        return response

    for header in [
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Credentials",
        "Access-Control-Max-Age",
        "Vary",
    ]:
        _delete_header(response.get("headers"), header)
        _delete_header(response.get("multiValueHeaders"), header)

    _set_single_header(response, "Access-Control-Allow-Origin", "*")

    method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
    )
    if method == "OPTIONS":
        _set_single_header(
            response,
            "Access-Control-Allow-Headers",
            "Origin, X-Requested-With, Content-Type, Accept, Authorization, stripe-signature",
        )
        _set_single_header(
            response,
            "Access-Control-Allow-Methods",
            "GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS",
        )
        _set_single_header(response, "Access-Control-Max-Age", "86400")

    return response


def get_event_type(event: dict[str, Any]) -> EventType:
    records = event.get("Records")
    if isinstance(records, list) and records:
        first = records[0]
        if first.get("eventSource") == "aws:sqs":
            return "sqs"
        if first.get("EventSource") == "aws:sns" or first.get("eventSource") == "aws:sns":
            return "sns"

    if event.get("httpMethod") or event.get("requestContext", {}).get("http"):
        return "http"

    route_key = event.get("requestContext", {}).get("routeKey")
    connection_id = event.get("requestContext", {}).get("connectionId")
    if route_key == "$connect":
        return "wsConnect"
    if route_key == "$disconnect":
        return "wsDisconnect"
    if connection_id and route_key in {"$default", "register", "unregister"}:
        return "wsDefault"

    if event.get("source") == "aws.events":
        return "scheduled"
    if event.get("source") == "serverless-plugin-warmup":
        return "warmup"
    if event.get("agentId") and event.get("message") and event.get("channel"):
        return "direct"

    return "unknown"


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    event_type = get_event_type(event or {})

    print("Event type detected:", event_type)
    print("Event details:", json.dumps(sanitize_event_for_log(event), default=str))

    if event_type == "http":
        response = asgi_handler(event, context)
        return normalize_cors_response(response, event)

    if event_type == "sqs":
        return handle_sqs_event(event, context)

    if event_type == "sns":
        return {"statusCode": 202, "body": "SNS event ignored"}

    if event_type in {"scheduled", "warmup"}:
        return {"statusCode": 200, "body": "OK"}

    if event_type == "wsConnect":
        return handle_ws_connect(event)

    if event_type == "wsDisconnect":
        return handle_ws_disconnect(event)

    if event_type == "wsDefault":
        return handle_ws_default(event)

    if event_type == "direct":
        return handle_direct_event(event, context)

    return {"statusCode": 400, "body": f"Unsupported event type {event_type}"}
