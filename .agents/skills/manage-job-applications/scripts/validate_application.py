from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from common import (
    ValidationError,
    canonical_digest,
    file_digest,
    load_json,
    parse_datetime,
    reject_extra_keys,
    require_enum,
    require_integer,
    require_keys,
    require_list,
    require_object,
    require_sha256,
    require_string,
    resolve_within,
    unique_strings,
    validate_against_schema,
)

EXACT_MAX_LIFETIME = timedelta(minutes=15)
BATCH_MAX_LIFETIME = timedelta(hours=24)


CHANNELS = {"EMAIL", "PORTAL", "LINKEDIN", "MANUAL"}
APPLICATION_FIELDS = {
    "schema_version", "application_id", "version", "candidate_id", "job_id",
    "channel", "sender_account_ref", "destination", "message", "answers",
    "artifacts", "payload_digest",
}
ARTIFACT_FIELDS = {
    "artifact_id", "candidate_id", "application_id", "path", "media_type",
    "byte_count", "sha256", "qa_status", "source_fact_ids",
}
BINDING_FIELDS = {
    "application_id", "version", "candidate_id", "job_id", "channel",
    "sender_account_ref", "destination", "payload_digest", "artifact_hashes",
    "claim_ledger_digest",
}
AUTHORIZATION_FIELDS = {
    "schema_version", "approval_id", "scope", "approver_ref", "issued_at",
    "expires_at", "bindings",
}


def validate_application(application: Any, artifact_root: Path) -> dict[str, Any]:
    validate_against_schema(application, "application.schema.json", "application")
    data = require_object(application, "application")
    require_keys(data, APPLICATION_FIELDS, "application")
    reject_extra_keys(data, APPLICATION_FIELDS, "application")
    if data["schema_version"] != "1.0":
        raise ValidationError("application.schema_version must be 1.0")
    application_id = require_string(data["application_id"], "application.application_id")
    require_integer(data["version"], "application.version", minimum=1)
    candidate_id = require_string(data["candidate_id"], "application.candidate_id")
    require_string(data["job_id"], "application.job_id")
    channel = require_enum(data["channel"], CHANNELS, "application.channel")
    if data["sender_account_ref"] is not None:
        require_string(data["sender_account_ref"], "application.sender_account_ref")
    if channel != "MANUAL" and data["sender_account_ref"] is None:
        raise ValidationError("application.sender_account_ref is required for external channels")
    require_string(data["destination"], "application.destination")
    require_string(data["message"], "application.message", allow_empty=True)

    for index, raw_answer in enumerate(require_list(data["answers"], "application.answers")):
        label = f"application.answers[{index}]"
        answer = require_object(raw_answer, label)
        fields = {"question", "answer", "status", "evidence_ids"}
        require_keys(answer, fields, label)
        reject_extra_keys(answer, fields, label)
        require_string(answer["question"], f"{label}.question")
        status = require_enum(answer["status"], {"VERIFIED", "UNKNOWN"}, f"{label}.status")
        evidence = unique_strings(answer["evidence_ids"], f"{label}.evidence_ids")
        if status == "UNKNOWN" and (answer["answer"] is not None or evidence):
            raise ValidationError(f"{label} cannot claim an answer or evidence while UNKNOWN")
        if status == "VERIFIED" and answer["answer"] is None:
            raise ValidationError(f"{label} needs a non-null answer when VERIFIED")
        if status == "VERIFIED" and not evidence:
            raise ValidationError(f"{label} needs evidence_ids when VERIFIED")
        if isinstance(answer["answer"], float):
            raise ValidationError(
                f"{label}.answer uses a float; encode exact values as strings or integers"
            )

    artifact_hashes: list[str] = []
    artifact_ids: set[str] = set()
    for index, raw_artifact in enumerate(require_list(data["artifacts"], "application.artifacts")):
        label = f"application.artifacts[{index}]"
        artifact = require_object(raw_artifact, label)
        require_keys(artifact, ARTIFACT_FIELDS, label)
        reject_extra_keys(artifact, ARTIFACT_FIELDS, label)
        artifact_id = require_string(artifact["artifact_id"], f"{label}.artifact_id")
        if artifact_id in artifact_ids:
            raise ValidationError(f"{label}.artifact_id is duplicated")
        artifact_ids.add(artifact_id)
        if artifact["candidate_id"] != candidate_id or artifact["application_id"] != application_id:
            raise ValidationError(f"{label} is bound to a different candidate or application")
        relative_path = require_string(artifact["path"], f"{label}.path")
        require_string(artifact["media_type"], f"{label}.media_type")
        expected_bytes = require_integer(artifact["byte_count"], f"{label}.byte_count", minimum=0)
        expected_hash = require_sha256(artifact["sha256"], f"{label}.sha256")
        require_enum(artifact["qa_status"], {"PASSED"}, f"{label}.qa_status")
        unique_strings(artifact["source_fact_ids"], f"{label}.source_fact_ids")
        resolved = resolve_within(artifact_root, relative_path)
        if not resolved.is_file():
            raise ValidationError(f"{label}.path does not exist: {relative_path}")
        actual_bytes, actual_hash = file_digest(resolved)
        if (expected_bytes, expected_hash) != (actual_bytes, actual_hash):
            raise ValidationError(f"{label} does not match the final artifact bytes")
        artifact_hashes.append(expected_hash)

    require_sha256(data["payload_digest"], "application.payload_digest")
    expected_payload = canonical_digest(data, omit={"payload_digest"})
    if data["payload_digest"] != expected_payload:
        raise ValidationError("application.payload_digest does not match canonical content")
    return {"artifact_hashes": artifact_hashes, "application": data}


def validate_authorization(
    authorization: Any,
    validated: dict[str, Any],
    at: datetime,
    *,
    claim_ledger_digest: str | None = None,
) -> None:
    validate_against_schema(authorization, "authorization.schema.json", "authorization")
    data = require_object(authorization, "authorization")
    require_keys(data, AUTHORIZATION_FIELDS, "authorization")
    reject_extra_keys(data, AUTHORIZATION_FIELDS, "authorization")
    if data["schema_version"] != "1.0":
        raise ValidationError("authorization.schema_version must be 1.0")
    require_string(data["approval_id"], "authorization.approval_id")
    scope = require_enum(data["scope"], {"EXACT", "BATCH"}, "authorization.scope")
    require_string(data["approver_ref"], "authorization.approver_ref")
    issued_at = parse_datetime(data["issued_at"], "authorization.issued_at")
    expires_at = parse_datetime(data["expires_at"], "authorization.expires_at")
    if expires_at <= issued_at:
        raise ValidationError("authorization.expires_at must be after issued_at")
    lifetime = expires_at - issued_at
    if scope == "EXACT" and lifetime > EXACT_MAX_LIFETIME:
        raise ValidationError(
            "EXACT authorization lifetime must not exceed 15 minutes"
        )
    if scope == "BATCH" and lifetime > BATCH_MAX_LIFETIME:
        raise ValidationError(
            "BATCH authorization lifetime must not exceed 24 hours"
        )
    if at.tzinfo is None:
        raise ValidationError("authorization validation time must include a timezone")
    validation_time = at.astimezone(timezone.utc)
    if validation_time < issued_at.astimezone(timezone.utc):
        raise ValidationError("authorization is not active before issued_at")
    if validation_time >= expires_at.astimezone(timezone.utc):
        raise ValidationError("authorization has expired")
    bindings = require_list(data["bindings"], "authorization.bindings")
    if not 1 <= len(bindings) <= 20:
        raise ValidationError("authorization.bindings must contain 1 to 20 items")
    if scope == "EXACT" and len(bindings) != 1:
        raise ValidationError("EXACT authorization must contain one binding")

    application = validated["application"]
    if claim_ledger_digest is None:
        raise ValidationError(
            "authorization requires a validated claim_ledger_digest"
        )
    claim_ledger_digest = require_sha256(
        claim_ledger_digest, "claim_ledger_digest"
    )
    matching = 0
    binding_keys: set[tuple[str, int, str, str | None, str]] = set()
    for index, raw_binding in enumerate(bindings):
        label = f"authorization.bindings[{index}]"
        binding = require_object(raw_binding, label)
        require_keys(binding, BINDING_FIELDS, label)
        reject_extra_keys(binding, BINDING_FIELDS, label)
        application_id = require_string(binding["application_id"], f"{label}.application_id")
        version = require_integer(binding["version"], f"{label}.version", minimum=1)
        channel = require_enum(binding["channel"], CHANNELS, f"{label}.channel")
        sender_account_ref = binding["sender_account_ref"]
        if sender_account_ref is not None:
            sender_account_ref = require_string(sender_account_ref, f"{label}.sender_account_ref")
        destination = require_string(binding["destination"], f"{label}.destination")
        binding_key = (application_id, version, channel, sender_account_ref, destination)
        if binding_key in binding_keys:
            raise ValidationError(f"{label} duplicates an application target in the authorization batch")
        binding_keys.add(binding_key)
        require_sha256(binding["payload_digest"], f"{label}.payload_digest")
        artifact_hashes = require_list(binding["artifact_hashes"], f"{label}.artifact_hashes")
        for hash_index, digest in enumerate(artifact_hashes):
            require_sha256(digest, f"{label}.artifact_hashes[{hash_index}]")
        require_sha256(
            binding["claim_ledger_digest"], f"{label}.claim_ledger_digest"
        )
        expected = {
            "application_id": application["application_id"],
            "version": application["version"],
            "candidate_id": application["candidate_id"],
            "job_id": application["job_id"],
            "channel": application["channel"],
            "sender_account_ref": application["sender_account_ref"],
            "destination": application["destination"],
            "payload_digest": application["payload_digest"],
            "artifact_hashes": validated["artifact_hashes"],
            "claim_ledger_digest": claim_ledger_digest,
        }
        if binding == expected:
            matching += 1
    if matching != 1:
        raise ValidationError("authorization does not contain exactly one matching immutable binding")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an application and its approval binding.")
    parser.add_argument("application", type=Path)
    parser.add_argument("authorization", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument(
        "--claim-ledger",
        type=Path,
        required=True,
        help="Claim ledger to validate against the profile and application before binding",
    )
    parser.add_argument(
        "--profile",
        type=Path,
        required=True,
        help="Candidate profile used to validate the claim ledger",
    )
    parser.add_argument("--at", help="ISO 8601 validation time; defaults to now")
    args = parser.parse_args()
    artifact_root = args.artifact_root or args.application.parent
    try:
        from validate_claims import validate_claims

        at = parse_datetime(args.at, "--at") if args.at else datetime.now(timezone.utc)
        application = load_json(args.application)
        validated = validate_application(application, artifact_root)
        ledger = load_json(args.claim_ledger)
        profile = load_json(args.profile)
        validate_claims(ledger, profile, application, artifact_root)
        claim_ledger_digest = require_sha256(
            require_object(ledger, "claim ledger")["ledger_digest"],
            "claim ledger.ledger_digest",
        )
        validate_authorization(
            load_json(args.authorization),
            validated,
            at,
            claim_ledger_digest=claim_ledger_digest,
        )
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    except KeyError as exc:
        print(f"INVALID: claim ledger is missing required field {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.application} + {args.authorization}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
