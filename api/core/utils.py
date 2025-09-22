from typing import Any, Dict


def to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def success_response(data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {"success": True, "data": data or {}}


