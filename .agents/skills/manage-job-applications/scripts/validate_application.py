from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
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
        if status == "VERIFIED" and not evidence:
            raise ValidationError(f"{label} needs evidence_ids when VERIFIED")

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
        qa_status = require_enum(artifact["qa_status"], {"PASSED", "FAILED", "PENDING"}, f"{label}.qa_status")
        if qa_status != "PASSED":
            raise ValidationError(f"{label}.qa_status must be PASSED for an immutable application package")
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


def validate_authorization(authorization: Any, validated: dict[str, Any], at: datetime) -> None:
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
    matching = 0
    for index, raw_binding in enumerate(bindings):
        label = f"authorization.bindings[{index}]"
        binding = require_object(raw_binding, label)
        require_keys(binding, BINDING_FIELDS, label)
        reject_extra_keys(binding, BINDING_FIELDS, label)
        require_integer(binding["version"], f"{label}.version", minimum=1)
        require_enum(binding["channel"], CHANNELS, f"{label}.channel")
        require_sha256(binding["payload_digest"], f"{label}.payload_digest")
        artifact_hashes = require_list(binding["artifact_hashes"], f"{label}.artifact_hashes")
        for hash_index, digest in enumerate(artifact_hashes):
            require_sha256(digest, f"{label}.artifact_hashes[{hash_index}]")
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
    parser.add_argument("--at", help="ISO 8601 validation time; defaults to now")
    args = parser.parse_args()
    artifact_root = args.artifact_root or args.application.parent
    try:
        at = parse_datetime(args.at, "--at") if args.at else datetime.now(timezone.utc)
        validated = validate_application(load_json(args.application), artifact_root)
        validate_authorization(load_json(args.authorization), validated, at)
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.application} + {args.authorization}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
