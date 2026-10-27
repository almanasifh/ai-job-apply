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
    "TRACKER": {"READ_OUTCOME_EVIDENCE", "VERIFY_OUTCOME"},
}
ROLE_INPUT_KINDS = {
    "SCOUT": {"PUBLIC_VACANCY"},
    "MATCHER": {"PUBLIC_VACANCY", "MINIMIZED_FACTS"},
    "DRAFTER": {"MATCH", "MINIMIZED_FACTS"},
    "VERIFIER": {
        "MATCH", "MINIMIZED_FACTS", "DRAFT_ARTIFACT", "CLAIM_LEDGER"
    },
    "TRACKER": {"OUTCOME_EVIDENCE", "CHECKPOINT_REFERENCE"},
}
ROLE_REQUIRED_INPUT_KINDS = {
    "SCOUT": {"PUBLIC_VACANCY"},
    "MATCHER": {"PUBLIC_VACANCY", "MINIMIZED_FACTS"},
    "DRAFTER": {"MATCH", "MINIMIZED_FACTS"},
    "VERIFIER": {
        "MATCH", "MINIMIZED_FACTS", "DRAFT_ARTIFACT", "CLAIM_LEDGER"
    },
    "TRACKER": {"OUTCOME_EVIDENCE"},
}
MAX_CONCURRENT_SPECIALISTS = 19


def validate_delegation(
    value: Any, at: datetime, *, require_active: bool = True
) -> dict[str, Any]:
    validate_against_schema(value, "delegation.schema.json", "delegation")
    data = require_object(value, "delegation")
    role = require_enum(data["role"], set(ROLE_CAPABILITIES), "delegation.role")
    capabilities = set(unique_strings(data["capabilities"], "delegation.capabilities"))
    if capabilities != ROLE_CAPABILITIES[role]:
        raise ValidationError(
            f"delegation.capabilities must exactly match the {role} capability set"
        )
    refs = unique_strings(data["input_refs"], "delegation.input_refs")
    if not refs:
        raise ValidationError("delegation must contain at least one input")
    digests = require_list(data["input_digests"], "delegation.input_digests")
    input_kinds = require_list(data["input_kinds"], "delegation.input_kinds")
    for index, kind in enumerate(input_kinds):
        require_enum(
            kind,
            ROLE_INPUT_KINDS[role],
            f"delegation.input_kinds[{index}]",
        )
    missing_input_kinds = ROLE_REQUIRED_INPUT_KINDS[role] - set(input_kinds)
    if missing_input_kinds:
        raise ValidationError(
            f"{role} delegation is missing required input kinds: "
            + ", ".join(sorted(missing_input_kinds))
        )
    for index, digest in enumerate(digests):
        require_sha256(digest, f"delegation.input_digests[{index}]")
    if len(refs) != len(digests) or len(refs) != len(input_kinds):
        raise ValidationError(
            "delegation input_refs, input_kinds, and input_digests must have equal length"
        )
    facts = unique_strings(
        data["permitted_fact_ids"], "delegation.permitted_fact_ids"
    )
    if role in {"SCOUT", "TRACKER"} and facts:
        raise ValidationError(
            f"{role} delegation cannot receive candidate fact identifiers"
        )
    if role == "SCOUT" and data["application_id"] is not None:
        raise ValidationError("SCOUT delegation.application_id must be null")
    if role != "SCOUT":
        application_id = require_string(
            data["application_id"], "delegation.application_id"
        )
        if not application_id.startswith("app_"):
            raise ValidationError(
                "delegation.application_id must start with app_"
            )
    issued = parse_datetime(data["issued_at"], "delegation.issued_at")
    expires = parse_datetime(data["expires_at"], "delegation.expires_at")
    if expires <= issued:
        raise ValidationError("delegation.expires_at must be after issued_at")
    if at.tzinfo is None:
        raise ValidationError("delegation validation time must include a timezone")
    current = at.astimezone(timezone.utc)
    if require_active and (
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


def validate_result(
    value: Any, delegation: dict[str, Any], at: datetime
) -> None:
    validate_against_schema(value, "specialist-result.schema.json", "result")
    data = require_object(value, "result")
    if (
        data["run_id"] != delegation["run_id"]
        or data["task_id"] != delegation["task_id"]
        or data["attempt_id"] != delegation["attempt_id"]
        or data["role"] != delegation["role"]
    ):
        raise ValidationError(
            "result is bound to a different delegation run or role"
        )
    require_sha256(data["task_digest"], "result.task_digest")
    if data["task_digest"] != delegation["task_digest"]:
        raise ValidationError("result is bound to a different delegation task")
    started = parse_datetime(data["started_at"], "result.started_at")
    completed = parse_datetime(data["completed_at"], "result.completed_at")
    if completed < started:
        raise ValidationError(
            "result.completed_at is earlier than started_at"
        )
    issued = parse_datetime(delegation["issued_at"], "delegation.issued_at")
    expires = parse_datetime(delegation["expires_at"], "delegation.expires_at")
    if started < issued or completed >= expires:
        raise ValidationError(
            "result execution must remain within the delegation validity window"
        )
    if at.tzinfo is None:
        raise ValidationError("result validation time must include a timezone")
    if completed > at.astimezone(timezone.utc):
        raise ValidationError("result cannot complete after validation time")
    refs = unique_strings(data["output_refs"], "result.output_refs")
    digests = require_list(data["output_digests"], "result.output_digests")
    for index, digest in enumerate(digests):
        require_sha256(digest, f"result.output_digests[{index}]")
    if len(refs) != len(digests):
        raise ValidationError(
            "result output_refs and output_digests must have equal length"
        )
    evidence_ids = unique_strings(data["evidence_ids"], "result.evidence_ids")
    unresolved = unique_strings(data["unresolved"], "result.unresolved")
    status = require_enum(
        data["status"],
        {"COMPLETED", "BLOCKED", "FAILED", "CANCELLED", "TIMED_OUT"},
        "result.status",
    )
    if status == "COMPLETED" and not refs:
        raise ValidationError(
            "completed result must contain at least one output reference"
        )
    if status != "COMPLETED" and (refs or evidence_ids):
        raise ValidationError(
            "non-completed result cannot provide outputs or evidence"
        )
    if status != "COMPLETED" and not unresolved:
        raise ValidationError(
            "non-completed result must explain the unresolved condition"
        )
    if data["role"] in {"SCOUT", "TRACKER"} and evidence_ids:
        raise ValidationError(
            f"{data['role']} result cannot cite candidate evidence identifiers"
        )
    if data["role"] in {"MATCHER", "DRAFTER", "VERIFIER"}:
        unauthorized = sorted(
            set(evidence_ids) - set(delegation["permitted_fact_ids"])
        )
        if unauthorized:
            raise ValidationError(
                "result evidence exceeds permitted delegation facts: "
                + ", ".join(unauthorized)
            )
    require_sha256(data["result_digest"], "result.result_digest")
    if data["result_digest"] != canonical_digest(
        data, omit={"result_digest"}
    ):
        raise ValidationError(
            "result.result_digest does not match canonical content"
        )


def validate_delegation_set(
    values: list[Any], at: datetime, *, require_active: bool = True
) -> list[dict[str, Any]]:
    if not values:
        raise ValidationError("delegation set must not be empty")
    delegations = [
        validate_delegation(value, at, require_active=require_active)
        for value in values
    ]
    run_ids = {delegation["run_id"] for delegation in delegations}
    if len(run_ids) != 1:
        raise ValidationError("delegation set must belong to one run")
    attempt_ids = [delegation["attempt_id"] for delegation in delegations]
    if len(attempt_ids) != len(set(attempt_ids)):
        raise ValidationError("delegation set contains a duplicate attempt")
    task_windows: dict[str, list[tuple[datetime, datetime]]] = {}
    events: list[tuple[datetime, int]] = []
    for delegation in delegations:
        issued = parse_datetime(delegation["issued_at"], "issued_at")
        expires = parse_datetime(delegation["expires_at"], "expires_at")
        for prior_issued, prior_expires in task_windows.setdefault(
            delegation["task_id"], []
        ):
            if issued < prior_expires and prior_issued < expires:
                raise ValidationError(
                    "delegation set contains overlapping attempts for one task"
                )
        task_windows[delegation["task_id"]].append((issued, expires))
        events.append((issued, 1))
        events.append((expires, -1))
    active = 0
    for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        active += delta
        if active > MAX_CONCURRENT_SPECIALISTS:
            raise ValidationError(
                "delegation set exceeds 19 concurrent specialist slots"
            )
    return delegations


def validate_result_set(
    pairs: list[tuple[Any, Any]], at: datetime
) -> None:
    delegations = validate_delegation_set(
        [delegation for delegation, _ in pairs],
        at,
        require_active=False,
    )
    claimed_outputs: set[str] = set()
    task_attempts: dict[str, list[tuple[datetime, str]]] = {}
    for delegation, (_, result) in zip(delegations, pairs):
        validate_result(result, delegation, at)
        result_data = require_object(result, "result")
        task_attempts.setdefault(delegation["task_id"], []).append(
            (
                parse_datetime(delegation["issued_at"], "delegation.issued_at"),
                result_data["status"],
            )
        )
        outputs = set(
            unique_strings(result_data["output_refs"], "result.output_refs")
        )
        conflicts = sorted(outputs & claimed_outputs)
        if conflicts:
            raise ValidationError(
                "specialist results claim the same output reference: "
                + ", ".join(conflicts)
            )
        claimed_outputs.update(outputs)
    for task_id, attempts in task_attempts.items():
        statuses = [status for _, status in sorted(attempts)]
        if "COMPLETED" in statuses[:-1]:
            raise ValidationError(
                "result set contains a retry after a completed task: " + task_id
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a bounded delegation and specialist result."
    )
    parser.add_argument("delegation", nargs="?", type=Path)
    parser.add_argument("result", nargs="?", type=Path)
    parser.add_argument(
        "--pair",
        action="append",
        nargs=2,
        type=Path,
        metavar=("DELEGATION", "RESULT"),
        help="validate one or more pairs as a bounded result set",
    )
    parser.add_argument("--at", help="ISO 8601 validation time; defaults to now")
    args = parser.parse_args()
    try:
        at = (
            parse_datetime(args.at, "--at")
            if args.at
            else datetime.now(timezone.utc)
        )
        if args.pair:
            if args.delegation is not None or args.result is not None:
                raise ValidationError(
                    "use either one positional pair or repeated --pair values"
                )
            pairs = [
                (load_json(delegation), load_json(result))
                for delegation, result in args.pair
            ]
            validate_result_set(pairs, at)
            label = f"{len(pairs)} delegation/result pairs"
        else:
            if args.delegation is None:
                raise ValidationError(
                    "provide a delegation or at least one --pair"
                )
            delegation = validate_delegation(
                load_json(args.delegation),
                at,
                require_active=args.result is None,
            )
            if args.result is None:
                label = f"active delegation {args.delegation}"
            else:
                validate_result(load_json(args.result), delegation, at)
                label = f"{args.delegation} + {args.result}"
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
