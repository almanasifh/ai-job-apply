from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SAFE_INTEGER_LIMIT = 9_007_199_254_740_991
SCHEMA_ROOT = Path(__file__).resolve().parents[1] / "references"
SCHEMA_KEYWORDS = {
    "$schema", "$id", "$ref", "title", "description", "type", "const",
    "enum", "pattern", "minLength", "minimum", "required", "properties",
    "additionalProperties", "items", "uniqueItems", "minItems", "maxItems",
    "format",
}


class ValidationError(ValueError):
    pass


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"JSON object contains duplicate key: {key}")
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> None:
    raise ValidationError(f"JSON contains unsupported numeric constant: {value}")


def parse_json_text(text: str, label: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_nonfinite_constant,
        )
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Cannot parse JSON from {label}: {exc}") from exc


def load_json(path: str | Path) -> Any:
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValidationError(f"Cannot read JSON from {source}: {exc}") from exc
    return parse_json_text(text, str(source))


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


def _matches_json_type(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    raise ValidationError(f"Schema uses unsupported JSON type: {expected}")


def _validate_schema_definition(schema: Any, label: str) -> None:
    if not isinstance(schema, dict):
        raise ValidationError(f"{label} must be an object")
    unsupported = sorted(set(schema) - SCHEMA_KEYWORDS)
    if unsupported:
        raise ValidationError(f"{label} uses unsupported keywords: {', '.join(unsupported)}")
    if "$ref" in schema and not isinstance(schema["$ref"], str):
        raise ValidationError(f"{label}.$ref must be a string")
    schema_type = schema.get("type")
    if schema_type is not None:
        types = schema_type if isinstance(schema_type, list) else [schema_type]
        if not types or any(not isinstance(item, str) for item in types) or len(types) != len(set(types)):
            raise ValidationError(f"{label}.type must be a string or non-empty string array")
        for item in types:
            _matches_json_type(None, item)
    required = schema.get("required", [])
    if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
        raise ValidationError(f"{label}.required must be a string array")
    if len(required) != len(set(required)):
        raise ValidationError(f"{label}.required must contain unique field names")
    if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
        raise ValidationError(f"{label}.enum must be a non-empty array")
    if "pattern" in schema:
        if not isinstance(schema["pattern"], str):
            raise ValidationError(f"{label}.pattern must be a string")
        try:
            re.compile(schema["pattern"])
        except re.error as exc:
            raise ValidationError(f"{label}.pattern is invalid: {exc}") from exc
    for keyword in ("minLength", "minItems", "maxItems"):
        if keyword in schema and (
            isinstance(schema[keyword], bool)
            or not isinstance(schema[keyword], int)
            or schema[keyword] < 0
        ):
            raise ValidationError(f"{label}.{keyword} must be a non-negative integer")
    if "minimum" in schema and (
        isinstance(schema["minimum"], bool)
        or not isinstance(schema["minimum"], (int, float))
        or not math.isfinite(schema["minimum"])
    ):
        raise ValidationError(f"{label}.minimum must be a finite number")
    if "uniqueItems" in schema and not isinstance(schema["uniqueItems"], bool):
        raise ValidationError(f"{label}.uniqueItems must be a boolean")
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise ValidationError(f"{label}.properties must be an object")
    for name, child in properties.items():
        _validate_schema_definition(child, f"{label}.properties.{name}")
    if "items" in schema:
        _validate_schema_definition(schema["items"], f"{label}.items")
    if "additionalProperties" in schema and not isinstance(schema["additionalProperties"], bool):
        raise ValidationError(f"{label}.additionalProperties must be a boolean")
    if "format" in schema and schema["format"] not in {"date-time", "uri"}:
        raise ValidationError(f"{label}.format is unsupported")


@lru_cache(maxsize=64)
def _load_schema_cached(path_value: str, _modified_ns: int, _byte_count: int) -> dict[str, Any]:
    path = Path(path_value)
    schema = require_object(load_json(path), f"schema {path.name}")
    _validate_schema_definition(schema, f"schema {path.name}")
    return schema


def _load_schema(path: Path, schema_root: Path) -> dict[str, Any]:
    resolved_root = schema_root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValidationError(f"Schema path escapes references root: {path}") from exc
    try:
        metadata = resolved.stat()
    except OSError as exc:
        raise ValidationError(f"Cannot inspect schema {resolved}: {exc}") from exc
    return _load_schema_cached(str(resolved), metadata.st_mtime_ns, metadata.st_size)


def _unique_json_items(items: list[Any]) -> bool:
    markers = [json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for item in items]
    return len(markers) == len(set(markers))


def _validate_schema_value(
    value: Any,
    schema: dict[str, Any],
    label: str,
    *,
    schema_path: Path,
    schema_root: Path,
) -> None:
    if "$ref" in schema:
        reference = schema["$ref"]
        if "#" in reference:
            raise ValidationError(f"{label} uses unsupported schema fragment: {reference}")
        referenced_path = schema_path.parent / reference
        referenced = _load_schema(referenced_path, schema_root)
        _validate_schema_value(
            value,
            referenced,
            label,
            schema_path=referenced_path.resolve(),
            schema_root=schema_root,
        )

    schema_type = schema.get("type")
    if schema_type is not None:
        expected_types = schema_type if isinstance(schema_type, list) else [schema_type]
        if not any(_matches_json_type(value, expected) for expected in expected_types):
            raise ValidationError(f"{label} must have JSON type {' or '.join(expected_types)}")

    if "const" in schema and value != schema["const"]:
        raise ValidationError(f"{label} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValidationError(f"{label} must be one of: {', '.join(map(str, schema['enum']))}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise ValidationError(f"{label} must contain at least {schema['minLength']} characters")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise ValidationError(f"{label} does not match required pattern")
        if schema.get("format") == "date-time":
            parse_datetime(value, label)
        elif schema.get("format") == "uri":
            parsed = urlsplit(value)
            if not parsed.scheme or any(char.isspace() for char in value):
                raise ValidationError(f"{label} must be an absolute URI")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValidationError(f"{label} must be at least {schema['minimum']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise ValidationError(f"{label} must contain at least {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ValidationError(f"{label} must contain at most {schema['maxItems']} items")
        if schema.get("uniqueItems") and not _unique_json_items(value):
            raise ValidationError(f"{label} must contain unique items")
        if "items" in schema:
            for index, item in enumerate(value):
                _validate_schema_value(
                    item,
                    schema["items"],
                    f"{label}[{index}]",
                    schema_path=schema_path,
                    schema_root=schema_root,
                )

    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = sorted(set(required) - value.keys())
        if missing:
            raise ValidationError(f"{label} is missing: {', '.join(missing)}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(value.keys() - properties.keys())
            if extra:
                raise ValidationError(f"{label} has unsupported fields: {', '.join(extra)}")
        for name, child_schema in properties.items():
            if name in value:
                _validate_schema_value(
                    value[name],
                    child_schema,
                    f"{label}.{name}",
                    schema_path=schema_path,
                    schema_root=schema_root,
                )


def validate_against_schema(
    value: Any,
    schema_name: str,
    label: str,
    *,
    schema_root: Path = SCHEMA_ROOT,
) -> None:
    schema_path = schema_root / schema_name
    schema = _load_schema(schema_path, schema_root)
    _validate_schema_value(
        value,
        schema,
        label,
        schema_path=schema_path.resolve(),
        schema_root=schema_root.resolve(),
    )


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
