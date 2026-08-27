import json
from typing import Any


def parse_params(raw: str | None, *required_keys: str) -> dict[str, Any]:
    if not raw:
        if required_keys:
            raise ValueError(f"Missing custom params; required keys: {required_keys}")
        return {}

    try:
        params = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid custom params JSON: {exc}") from exc

    if not isinstance(params, dict):
        raise ValueError(f"Custom params must be a JSON object, got {type(params).__name__}")

    missing = [key for key in required_keys if key not in params]
    if missing:
        raise ValueError(f"Missing required custom params: {missing}")

    return params
