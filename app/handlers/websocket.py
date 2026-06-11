import json
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings


def _json_response(status_code: int, body: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "body": json.dumps(body or {}, default=str),
    }


def _safe_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _connection_table():
    settings = get_settings()
    if not settings.connections_table:
        return None
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    return dynamodb.Table(settings.connections_table)


def _management_endpoint(event: dict[str, Any]) -> str | None:
    settings = get_settings()
    if settings.ws_endpoint:
        return settings.ws_endpoint.replace("wss://", "https://").replace("ws://", "http://")

    request_context = event.get("requestContext", {})
    domain_name = request_context.get("domainName")
    stage = request_context.get("stage")
    if not domain_name or not stage:
        return None

    return f"https://{domain_name}/{stage}"


def _ws_client(event: dict[str, Any]):
    endpoint_url = _management_endpoint(event)
    if not endpoint_url:
        raise RuntimeError("WebSocket management endpoint could not be resolved")
    return boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=endpoint_url,
        region_name=get_settings().aws_region,
    )


def handle_ws_connect(event: dict[str, Any]) -> dict[str, Any]:
    connection_id = event.get("requestContext", {}).get("connectionId")
    if not connection_id:
        return _json_response(400, {"message": "connectionId is required"})

    query = event.get("queryStringParameters") or {}
    table = _connection_table()
    if table:
        table.put_item(
            Item={
                "connectionId": connection_id,
                "roomId": query.get("roomId") or query.get("channelId") or query.get("convId"),
                "channelId": query.get("channelId"),
                "convId": query.get("convId"),
                "actor": query.get("actor"),
                "agentId": query.get("agentId"),
                "updatedAt": datetime.now(timezone.utc).isoformat(),
            }
        )

    return {"statusCode": 200}


def handle_ws_disconnect(event: dict[str, Any]) -> dict[str, Any]:
    connection_id = event.get("requestContext", {}).get("connectionId")
    if not connection_id:
        return _json_response(400, {"message": "connectionId is required"})

    table = _connection_table()
    if table:
        table.delete_item(Key={"connectionId": connection_id})

    return {"statusCode": 200}


def handle_ws_default(event: dict[str, Any]) -> dict[str, Any]:
    connection_id = event.get("requestContext", {}).get("connectionId")
    if not connection_id:
        return _json_response(400, {"message": "connectionId is required"})

    body = _safe_json(event.get("body"))
    action = body.get("action")

    if action in {"register", "heartbeat"}:
        return _register_or_heartbeat(connection_id, body)

    if action == "broadcast":
        return _broadcast(event, body)

    _post_to_connection(
        event,
        connection_id,
        {
            "type": "echo",
            "connectionId": connection_id,
            "payload": body,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    return {"statusCode": 200}


def _register_or_heartbeat(connection_id: str, body: dict[str, Any]) -> dict[str, Any]:
    table = _connection_table()
    if table:
        table.update_item(
            Key={"connectionId": connection_id},
            UpdateExpression=(
                "SET roomId = :roomId, channelId = :channelId, convId = :convId, "
                "actor = :actor, agentId = :agentId, updatedAt = :updatedAt"
            ),
            ExpressionAttributeValues={
                ":roomId": body.get("roomId") or body.get("channelId") or body.get("convId"),
                ":channelId": body.get("channelId"),
                ":convId": body.get("convId"),
                ":actor": body.get("actor"),
                ":agentId": body.get("agentId"),
                ":updatedAt": datetime.now(timezone.utc).isoformat(),
            },
        )
    return {"statusCode": 200}


def _broadcast(event: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    payload = body.get("payload") or {}
    table = _connection_table()
    if not table:
        return _json_response(500, {"message": "CONNECTIONS_TABLE is not configured"})

    scan_result = table.scan(ProjectionExpression="connectionId")
    connections = scan_result.get("Items", [])

    for item in connections:
        target_connection_id = item.get("connectionId")
        if target_connection_id:
            _post_to_connection(event, target_connection_id, payload)

    return {"statusCode": 200}


def _post_to_connection(
    event: dict[str, Any],
    connection_id: str,
    payload: dict[str, Any],
) -> None:
    try:
        _ws_client(event).post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(payload, default=str).encode("utf-8"),
        )
    except ClientError as exc:
        status_code = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status_code == 410:
            table = _connection_table()
            if table:
                table.delete_item(Key={"connectionId": connection_id})
            return
        raise
