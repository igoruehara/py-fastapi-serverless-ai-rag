from __future__ import annotations

import json
from typing import Any


def normalize_extra_fields(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return {}
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {"value": value}
        return normalize_extra_fields(parsed)
    if isinstance(value, dict):
        return {str(key): _normalize_value(item) for key, item in value.items()}
    return {"value": _normalize_value(value)}


def _normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, str):
        clean = value.strip()
        lower = clean.lower()
        if lower == "true":
            return True
        if lower == "false":
            return False
        if _looks_int(clean):
            return int(clean)
        if _looks_float(clean):
            return float(clean)
        return clean
    return value


def _looks_int(value: str) -> bool:
    if not value:
        return False
    return value.isdigit() or (value[0] == "-" and value[1:].isdigit())


def _looks_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return "." in value
