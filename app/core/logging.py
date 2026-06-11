from copy import deepcopy
from typing import Any

SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-internal-secret",
    "x-fique-internal-secret",
    "x-postou-ganhou-internal-secret",
}


def _redact_headers(headers: Any) -> None:
    if not isinstance(headers, dict):
        return
    for key in list(headers.keys()):
        if key.lower() in SENSITIVE_HEADERS:
            headers[key] = "[REDACTED]"


def sanitize_event_for_log(event: Any) -> Any:
    clone = deepcopy(event or {})
    if not isinstance(clone, dict):
        return clone

    _redact_headers(clone.get("headers"))
    _redact_headers(clone.get("multiValueHeaders"))

    if clone.get("body"):
        clone["body"] = "[REDACTED]"

    return clone
