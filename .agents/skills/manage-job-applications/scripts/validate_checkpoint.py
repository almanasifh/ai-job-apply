from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import (
    ValidationError,
    canonical_digest,
    parse_datetime,
    parse_json_text,
    reject_extra_keys,
    require_enum,
    require_integer,
    require_keys,
    require_object,
    require_sha256,
    require_string,
    unique_strings,
    validate_against_schema,
)


STATUSES = {
    "RESEARCHED", "ROUTED", "PREPARING", "READY", "NEEDS_INPUT",
    "NEEDS_VERIFICATION", "TECHNICAL_HOLD", "SUBMISSION_UNCERTAIN",
    "SENT", "SUBMITTED", "DELIVERY_FAILED", "SUBMISSION_FAILED", "SKIPPED",
}
EVENT_FIELDS = {
    "schema_version", "event_id", "sequence", "application_id", "occurred_at",
    "event_type", "workflow_status", "actor", "attempt_id", "evidence_refs",
    "previous_event_hash", "event_hash",
}
ACTION_STATUSES = {
    "SUBMISSION_UNCERTAIN", "SENT", "SUBMITTED", "DELIVERY_FAILED",
    "SUBMISSION_FAILED",
}


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ValidationError(f"Cannot read checkpoint {path}: {exc}") from exc
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        events.append(require_object(parse_json_text(line, f"line {line_number}"), f"line {line_number}"))
    if not events:
        raise ValidationError("checkpoint must contain at least one event")
    return events


def validate_checkpoint(events: list[dict[str, Any]]) -> None:
    previous_hash: str | None = None
    previous_time = None
    event_ids: set[str] = set()
    application_id: str | None = None
    for index, event in enumerate(events, 1):
        label = f"event {index}"
        validate_against_schema(event, "event.schema.json", label)
        require_keys(event, EVENT_FIELDS, label)
        reject_extra_keys(event, EVENT_FIELDS, label)
        if event["schema_version"] != "1.0":
            raise ValidationError(f"{label}.schema_version must be 1.0")
        event_id = require_string(event["event_id"], f"{label}.event_id")
        if event_id in event_ids:
            raise ValidationError(f"{label}.event_id is duplicated")
        event_ids.add(event_id)
        if require_integer(event["sequence"], f"{label}.sequence", minimum=1) != index:
            raise ValidationError(f"{label}.sequence must be {index}")
        current_application = require_string(event["application_id"], f"{label}.application_id")
        if application_id is None:
            application_id = current_application
        elif current_application != application_id:
            raise ValidationError(f"{label}.application_id changed within the checkpoint")
        occurred_at = parse_datetime(event["occurred_at"], f"{label}.occurred_at")
        if previous_time is not None and occurred_at < previous_time:
            raise ValidationError(f"{label}.occurred_at is earlier than the prior event")
        previous_time = occurred_at
        require_string(event["event_type"], f"{label}.event_type")
        workflow_status = require_enum(event["workflow_status"], STATUSES, f"{label}.workflow_status")
        require_string(event["actor"], f"{label}.actor")
        if event["attempt_id"] is not None:
            require_string(event["attempt_id"], f"{label}.attempt_id")
        evidence_refs = unique_strings(event["evidence_refs"], f"{label}.evidence_refs")
        if workflow_status in ACTION_STATUSES:
            if event["attempt_id"] is None:
                raise ValidationError(f"{label}.attempt_id is required for {workflow_status}")
            if not evidence_refs:
                raise ValidationError(f"{label}.evidence_refs is required for {workflow_status}")
        if event["previous_event_hash"] != previous_hash:
            raise ValidationError(f"{label}.previous_event_hash does not match the prior event")
        event_hash = require_sha256(event["event_hash"], f"{label}.event_hash")
        expected = canonical_digest(event, omit={"event_hash"})
        if event_hash != expected:
            raise ValidationError(f"{label}.event_hash does not match its canonical content")
        previous_hash = event_hash


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an append-only checkpoint JSONL file.")
    parser.add_argument("checkpoint", type=Path)
    args = parser.parse_args()
    try:
        validate_checkpoint(load_events(args.checkpoint))
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.checkpoint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
