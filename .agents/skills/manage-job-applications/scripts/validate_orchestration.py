from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import (
    ValidationError,
    canonical_digest,
    load_json,
    parse_datetime,
    require_enum,
    require_list,
    require_object,
    require_sha256,
    require_string,
    unique_strings,
    validate_against_schema,
)


ROLE_CAPABILITIES = {
    "SCOUT": {"READ_PUBLIC"},
    "MATCHER": {"READ_PUBLIC", "READ_MINIMIZED_FACTS", "DRAFT_STRUCTURED"},
    "DRAFTER": {"READ_MINIMIZED_FACTS", "DRAFT_CONTENT"},
    "VERIFIER": {"READ_MINIMIZED_FACTS", "VERIFY_CONTENT"},
    "OUTCOME_AUDITOR": {"READ_OUTCOME_EVIDENCE", "VERIFY_OUTCOME"},
}


def validate_delegation(value: Any, at: datetime) -> dict[str, Any]:
    validate_against_schema(value, "delegation.schema.json", "delegation")
    data = require_object(value, "delegation")
    role = require_enum(data["role"], set(ROLE_CAPABILITIES), "delegation.role")
    capabilities = set(unique_strings(data["capabilities"], "delegation.capabilities"))
    if capabilities != ROLE_CAPABILITIES[role]:
        raise ValidationError(
            f"delegation.capabilities must exactly match the {role} capability set"
        )
    refs = unique_strings(data["input_refs"], "delegation.input_refs")
    digests = require_list(data["input_digests"], "delegation.input_digests")
    for index, digest in enumerate(digests):
        require_sha256(digest, f"delegation.input_digests[{index}]")
    if len(refs) != len(digests):
        raise ValidationError(
            "delegation input_refs and input_digests must have equal length"
        )
    facts = unique_strings(
        data["permitted_fact_ids"], "delegation.permitted_fact_ids"
    )
    if role in {"SCOUT", "OUTCOME_AUDITOR"} and facts:
        raise ValidationError(
            f"{role} delegation cannot receive candidate fact identifiers"
        )
    issued = parse_datetime(data["issued_at"], "delegation.issued_at")
    expires = parse_datetime(data["expires_at"], "delegation.expires_at")
    if expires <= issued:
        raise ValidationError("delegation.expires_at must be after issued_at")
    current = at.astimezone(timezone.utc)
    if (
        current < issued.astimezone(timezone.utc)
        or current >= expires.astimezone(timezone.utc)
    ):
        raise ValidationError("delegation is not active at validation time")
    require_sha256(data["task_digest"], "delegation.task_digest")
    if data["task_digest"] != canonical_digest(data, omit={"task_digest"}):
        raise ValidationError(
            "delegation.task_digest does not match canonical content"
        )
    return data


def validate_result(value: Any, delegation: dict[str, Any]) -> None:
    validate_against_schema(value, "specialist-result.schema.json", "result")
    data = require_object(value, "result")
    if (
        data["run_id"] != delegation["run_id"]
        or data["role"] != delegation["role"]
    ):
        raise ValidationError(
            "result is bound to a different delegation run or role"
        )
    started = parse_datetime(data["started_at"], "result.started_at")
    completed = parse_datetime(data["completed_at"], "result.completed_at")
    if completed < started:
        raise ValidationError(
            "result.completed_at is earlier than started_at"
        )
    refs = unique_strings(data["output_refs"], "result.output_refs")
    digests = require_list(data["output_digests"], "result.output_digests")
    for index, digest in enumerate(digests):
        require_sha256(digest, f"result.output_digests[{index}]")
    if len(refs) != len(digests):
        raise ValidationError(
            "result output_refs and output_digests must have equal length"
        )
    status = require_string(data["status"], "result.status")
    if status == "COMPLETED" and not refs:
        raise ValidationError(
            "completed result must contain at least one output reference"
        )
    require_sha256(data["result_digest"], "result.result_digest")
    if data["result_digest"] != canonical_digest(
        data, omit={"result_digest"}
    ):
        raise ValidationError(
            "result.result_digest does not match canonical content"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a bounded delegation and specialist result."
    )
    parser.add_argument("delegation", type=Path)
    parser.add_argument("result", type=Path)
    parser.add_argument("--at", help="ISO 8601 validation time; defaults to now")
    args = parser.parse_args()
    try:
        at = (
            parse_datetime(args.at, "--at")
            if args.at
            else datetime.now(timezone.utc)
        )
        delegation = validate_delegation(load_json(args.delegation), at)
        validate_result(load_json(args.result), delegation)
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.delegation} + {args.result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
