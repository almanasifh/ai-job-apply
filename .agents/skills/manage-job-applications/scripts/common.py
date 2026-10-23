from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SAFE_INTEGER_LIMIT = 9_007_199_254_740_991


class ValidationError(ValueError):
    pass


def load_json(path: str | Path) -> Any:
    source = Path(path)
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"Cannot read JSON from {source}: {exc}") from exc


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{label} must be an array")
    return value


def require_string(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value):
        raise ValidationError(f"{label} must be a non-empty string")
    return value


def require_integer(value: Any, label: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise ValidationError(f"{label} must be at least {minimum}")
    return value


def require_keys(value: dict[str, Any], required: Iterable[str], label: str) -> None:
    missing = sorted(set(required) - value.keys())
    if missing:
        raise ValidationError(f"{label} is missing: {', '.join(missing)}")


def reject_extra_keys(value: dict[str, Any], allowed: Iterable[str], label: str) -> None:
    extra = sorted(value.keys() - set(allowed))
    if extra:
        raise ValidationError(f"{label} has unsupported fields: {', '.join(extra)}")


def require_enum(value: Any, allowed: set[str], label: str) -> str:
    item = require_string(value, label)
    if item not in allowed:
        raise ValidationError(f"{label} must be one of: {', '.join(sorted(allowed))}")
    return item


def require_sha256(value: Any, label: str) -> str:
    item = require_string(value, label)
    if not SHA256_PATTERN.fullmatch(item):
        raise ValidationError(f"{label} must be a lowercase SHA-256 digest")
    return item


def parse_datetime(value: Any, label: str) -> datetime:
    item = require_string(value, label)
    try:
        parsed = datetime.fromisoformat(item.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{label} must be an ISO 8601 date-time") from exc
    if parsed.tzinfo is None:
        raise ValidationError(f"{label} must include a timezone")
    return parsed


def unique_strings(value: Any, label: str) -> list[str]:
    items = require_list(value, label)
    result = [require_string(item, f"{label}[{index}]") for index, item in enumerate(items)]
    if len(result) != len(set(result)):
        raise ValidationError(f"{label} must contain unique values")
    return result


def _validate_jcs_value(value: Any, label: str = "value") -> None:
    if value is None or isinstance(value, (str, bool)):
        if isinstance(value, str) and any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise ValidationError(f"{label} contains an unpaired Unicode surrogate")
        return
    if isinstance(value, int):
        if abs(value) > SAFE_INTEGER_LIMIT:
            raise ValidationError(f"{label} exceeds the interoperable JCS integer range")
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValidationError(f"{label} contains a non-finite number")
        raise ValidationError(f"{label} uses a float; encode exact values as strings or integers")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_jcs_value(item, f"{label}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValidationError(f"{label} contains a non-string object key")
            _validate_jcs_value(key, f"{label} key")
            _validate_jcs_value(item, f"{label}.{key}")
        return
    raise ValidationError(f"{label} contains unsupported type {type(value).__name__}")


def _utf16_sort_key(value: str) -> bytes:
    return value.encode("utf-16-be")


def _serialize_jcs(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(_serialize_jcs(item) for item in value) + "]"
    if isinstance(value, dict):
        keys = sorted(value, key=_utf16_sort_key)
        return "{" + ",".join(
            f"{_serialize_jcs(key)}:{_serialize_jcs(value[key])}" for key in keys
        ) + "}"
    raise ValidationError(f"Unsupported JCS type {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Return RFC 8785 bytes for the integer-only JSON subset used by this project."""
    _validate_jcs_value(value)
    return _serialize_jcs(value).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_digest(value: dict[str, Any], *, omit: Iterable[str] = ()) -> str:
    omitted = set(omit)
    payload = {key: item for key, item in value.items() if key not in omitted}
    return sha256_bytes(canonical_json_bytes(payload))


def file_digest(path: str | Path) -> tuple[int, str]:
    source = Path(path)
    digest = hashlib.sha256()
    byte_count = 0
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            byte_count += len(chunk)
            digest.update(chunk)
    return byte_count, digest.hexdigest()


def resolve_within(root: str | Path, relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise ValidationError(f"Artifact path must be relative: {relative_path}")
    resolved_root = Path(root).resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValidationError(f"Artifact path escapes its root: {relative_path}") from exc
    return resolved
