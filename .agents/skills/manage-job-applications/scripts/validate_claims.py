from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import (
    ValidationError,
    canonical_digest,
    load_json,
    require_enum,
    require_list,
    require_object,
    require_sha256,
    require_string,
    unique_strings,
    validate_against_schema,
)
from validate_application import validate_application
from validate_profile import validate_profile


def validate_claims(
    ledger: Any,
    profile: Any,
    application: Any,
    artifact_root: Path,
) -> None:
    validate_against_schema(
        ledger, "claim-ledger.schema.json", "claim ledger"
    )
    data = require_object(ledger, "claim ledger")
    validate_profile(profile)
    validated_application = validate_application(application, artifact_root)
    profile_data = require_object(profile, "profile")
    application_data = validated_application["application"]
    if data["candidate_id"] != profile_data.get("candidate_id"):
        raise ValidationError(
            "claim ledger candidate_id does not match profile"
        )
    if data["application_id"] != application_data.get("application_id"):
        raise ValidationError(
            "claim ledger application_id does not match application"
        )
    if (
        data["application_version"] != application_data["version"]
        or data["application_digest"] != application_data["payload_digest"]
    ):
        raise ValidationError(
            "claim ledger is not bound to the exact application package"
        )
    facts = {
        require_string(item["id"], "profile fact id"): item
        for item in require_list(profile_data.get("facts"), "profile.facts")
    }
    artifacts = {
        require_string(item["artifact_id"], "artifact id"): item
        for item in require_list(
            application_data.get("artifacts"), "application.artifacts"
        )
    }
    claim_ids: set[str] = set()
    covered_artifact_facts: set[tuple[str, str]] = set()
    covered_screening_facts: set[str] = set()
    message_covered = False
    message = require_string(
        application_data.get("message"), "application.message", allow_empty=True
    )
    for index, raw_claim in enumerate(
        require_list(data["claims"], "claim ledger.claims")
    ):
        label = f"claim ledger.claims[{index}]"
        claim = require_object(raw_claim, label)
        claim_id = require_string(claim["claim_id"], f"{label}.claim_id")
        if claim_id in claim_ids:
            raise ValidationError(f"{label}.claim_id is duplicated")
        claim_ids.add(claim_id)
        claim_text = require_string(claim["text"], f"{label}.text")
        status = require_enum(
            claim["status"],
            {"VERIFIED", "UNKNOWN", "REJECTED"},
            f"{label}.status",
        )
        use = require_enum(
            claim["use"],
            {"CV", "COVER_LETTER", "SCREENING", "CONTACT"},
            f"{label}.use",
        )
        evidence_ids = unique_strings(
            claim["evidence_ids"], f"{label}.evidence_ids"
        )
        artifact_ids = unique_strings(
            claim["artifact_ids"], f"{label}.artifact_ids"
        )
        unknown_artifacts = sorted(set(artifact_ids) - artifacts.keys())
        if unknown_artifacts:
            raise ValidationError(
                f"{label}.artifact_ids is unknown: "
                + ", ".join(unknown_artifacts)
            )
        if status == "VERIFIED" and not evidence_ids:
            raise ValidationError(
                f"{label}.evidence_ids is required for VERIFIED"
            )
        if status != "VERIFIED" and evidence_ids:
            raise ValidationError(
                f"{label}.evidence_ids must be empty unless VERIFIED"
            )
        if status != "VERIFIED" and artifact_ids:
            raise ValidationError(
                f"{label}.artifact_ids must be empty unless VERIFIED"
            )
        for evidence_id in evidence_ids:
            fact = facts.get(evidence_id)
            if fact is None:
                raise ValidationError(
                    f"{label}.evidence_ids is unknown: {evidence_id}"
                )
            if fact.get("status") != "VERIFIED":
                raise ValidationError(
                    f"{label}.evidence_ids is not VERIFIED: {evidence_id}"
                )
            if use not in fact.get("allowed_uses", []):
                raise ValidationError(
                    f"{label} uses {evidence_id} outside its allowed uses"
                )
        for artifact_id in artifact_ids:
            artifact_fact_ids = set(
                unique_strings(
                    artifacts[artifact_id]["source_fact_ids"],
                    f"artifact {artifact_id}.source_fact_ids",
                )
            )
            unsupported = sorted(set(evidence_ids) - artifact_fact_ids)
            if unsupported:
                raise ValidationError(
                    f"{label} uses facts not declared by artifact {artifact_id}: "
                    + ", ".join(unsupported)
                )
            covered_artifact_facts.update(
                (artifact_id, evidence_id) for evidence_id in evidence_ids
            )
        if status == "VERIFIED" and use == "SCREENING":
            covered_screening_facts.update(evidence_ids)
        if (
            status == "VERIFIED"
            and use in {"COVER_LETTER", "CONTACT"}
            and claim_text
            and claim_text in message
        ):
            message_covered = True
    required_answer_facts: set[str] = set()
    for index, raw_answer in enumerate(
        require_list(application_data.get("answers"), "application.answers")
    ):
        label = f"application.answers[{index}]"
        answer = require_object(raw_answer, label)
        evidence_ids = unique_strings(
            answer["evidence_ids"], f"{label}.evidence_ids"
        )
        missing_evidence = sorted(set(evidence_ids) - facts.keys())
        if missing_evidence:
            raise ValidationError(
                f"{label}.evidence_ids is unknown: "
                + ", ".join(missing_evidence)
            )
        if answer.get("status") == "VERIFIED":
            unverified = sorted(
                evidence_id
                for evidence_id in evidence_ids
                if facts[evidence_id].get("status") != "VERIFIED"
            )
            if unverified:
                raise ValidationError(
                    f"{label}.evidence_ids is not VERIFIED: "
                    + ", ".join(unverified)
                )
            required_answer_facts.update(evidence_ids)
    required_artifact_facts = {
        (artifact_id, fact_id)
        for artifact_id, artifact in artifacts.items()
        for fact_id in unique_strings(
            artifact["source_fact_ids"],
            f"artifact {artifact_id}.source_fact_ids",
        )
    }
    missing = sorted(required_artifact_facts - covered_artifact_facts)
    if missing:
        raise ValidationError(
            "claim ledger does not cover artifact source facts: "
            + ", ".join(f"{artifact_id}:{fact_id}" for artifact_id, fact_id in missing)
        )
    missing_answers = sorted(required_answer_facts - covered_screening_facts)
    if missing_answers:
        raise ValidationError(
            "claim ledger does not cover application answer evidence: "
            + ", ".join(missing_answers)
        )
    if message.strip() and not message_covered:
        raise ValidationError(
            "claim ledger does not cover application message with a "
            "COVER_LETTER or CONTACT claim"
        )
    require_sha256(data["ledger_digest"], "claim ledger.ledger_digest")
    if data["ledger_digest"] != canonical_digest(
        data, omit={"ledger_digest"}
    ):
        raise ValidationError(
            "claim ledger.ledger_digest does not match canonical content"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate employer-facing claims against verified permitted facts."
        )
    )
    parser.add_argument("ledger", type=Path)
    parser.add_argument("profile", type=Path)
    parser.add_argument("application", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    args = parser.parse_args()
    try:
        artifact_root = args.artifact_root or args.application.parent
        validate_claims(
            load_json(args.ledger),
            load_json(args.profile),
            load_json(args.application),
            artifact_root,
        )
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
