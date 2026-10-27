from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import (
    ValidationError,
    canonical_digest,
    filesystem_error_reason,
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
SPECIALIST_ACTORS = frozenset(
    {"scout", "matcher", "drafter", "verifier", "tracker"}
)
INITIAL_STATUSES = frozenset({"RESEARCHED", "SKIPPED"})
STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "RESEARCHED": frozenset({
        "ROUTED", "PREPARING", "READY", "NEEDS_INPUT", "NEEDS_VERIFICATION",
        "TECHNICAL_HOLD", "SKIPPED",
    }),
    "ROUTED": frozenset({
        "PREPARING", "READY", "NEEDS_INPUT", "NEEDS_VERIFICATION",
        "TECHNICAL_HOLD", "SKIPPED",
    }),
    "PREPARING": frozenset({
        "PREPARING", "READY", "NEEDS_INPUT", "NEEDS_VERIFICATION",
        "TECHNICAL_HOLD", "SKIPPED",
    }),
    "READY": frozenset({
        "READY", "PREPARING", "NEEDS_INPUT", "NEEDS_VERIFICATION",
        "TECHNICAL_HOLD", "SENT", "SUBMITTED", "SUBMISSION_UNCERTAIN",
        "SUBMISSION_FAILED", "SKIPPED",
    }),
    "NEEDS_INPUT": frozenset({
        "PREPARING", "READY", "NEEDS_INPUT", "NEEDS_VERIFICATION",
        "TECHNICAL_HOLD", "SKIPPED",
    }),
    "NEEDS_VERIFICATION": frozenset({
        "PREPARING", "READY", "NEEDS_INPUT", "NEEDS_VERIFICATION",
        "TECHNICAL_HOLD", "SKIPPED",
    }),
    "TECHNICAL_HOLD": frozenset({
        "TECHNICAL_HOLD", "PREPARING", "READY", "NEEDS_INPUT",
        "NEEDS_VERIFICATION", "SKIPPED",
    }),
    "SENT": frozenset({
        "SUBMITTED", "DELIVERY_FAILED", "SUBMISSION_UNCERTAIN", "TECHNICAL_HOLD",
    }),
    "SUBMITTED": frozenset({"DELIVERY_FAILED", "TECHNICAL_HOLD"}),
    "DELIVERY_FAILED": frozenset({
        "TECHNICAL_HOLD", "NEEDS_VERIFICATION", "SKIPPED",
    }),
    "SUBMISSION_FAILED": frozenset({
        "PREPARING", "READY", "TECHNICAL_HOLD", "NEEDS_INPUT",
        "NEEDS_VERIFICATION", "SKIPPED",
    }),
    "SUBMISSION_UNCERTAIN": frozenset({
        "SENT", "SUBMITTED", "DELIVERY_FAILED", "SUBMISSION_FAILED",
        "TECHNICAL_HOLD", "NEEDS_VERIFICATION",
    }),
    "SKIPPED": frozenset(),
}


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValidationError(f"Cannot read checkpoint {path.name}: {filesystem_error_reason(exc)}") from exc
    except UnicodeError as exc:
        raise ValidationError(f"Checkpoint {path.name} is not valid UTF-8") from exc
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        events.append(require_object(parse_json_text(line, f"line {line_number}"), f"line {line_number}"))
    if not events:
        raise ValidationError("checkpoint must contain at least one event")
    return events


def _reject_specialist_actor(actor: str, label: str) -> None:
    if actor.casefold() in SPECIALIST_ACTORS:
        raise ValidationError(
            f"{label}.actor cannot be a specialist role; only the main agent "
            "writes the canonical checkpoint"
        )


def validate_checkpoint(events: list[dict[str, Any]]) -> None:
    previous_hash: str | None = None
    previous_time = None
    previous_status: str | None = None
    previous_attempt_id: str | None = None
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
        actor = require_string(event["actor"], f"{label}.actor")
        _reject_specialist_actor(actor, label)
        attempt_id = event["attempt_id"]
        if attempt_id is not None:
            attempt_id = require_string(attempt_id, f"{label}.attempt_id")
        evidence_refs = unique_strings(event["evidence_refs"], f"{label}.evidence_refs")
        if workflow_status in ACTION_STATUSES:
            if attempt_id is None:
                raise ValidationError(f"{label}.attempt_id is required for {workflow_status}")
            if not evidence_refs:
                raise ValidationError(f"{label}.evidence_refs is required for {workflow_status}")
        if previous_status is None:
            if workflow_status not in INITIAL_STATUSES:
                raise ValidationError(
                    f"{label}.workflow_status must start as RESEARCHED or SKIPPED"
                )
        else:
            allowed = STATUS_TRANSITIONS[previous_status]
            if workflow_status not in allowed:
                raise ValidationError(
                    f"{label}.workflow_status cannot follow {previous_status}"
                )
            if previous_status == "SUBMISSION_UNCERTAIN":
                if attempt_id is None or attempt_id != previous_attempt_id:
                    raise ValidationError(
                        f"{label}.attempt_id must reuse the SUBMISSION_UNCERTAIN "
                        "attempt; blind retries are forbidden"
                    )
        if event["previous_event_hash"] != previous_hash:
            raise ValidationError(f"{label}.previous_event_hash does not match the prior event")
        event_hash = require_sha256(event["event_hash"], f"{label}.event_hash")
        expected = canonical_digest(event, omit={"event_hash"})
        if event_hash != expected:
            raise ValidationError(f"{label}.event_hash does not match its canonical content")
        previous_hash = event_hash
        previous_status = workflow_status
        previous_attempt_id = attempt_id


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
