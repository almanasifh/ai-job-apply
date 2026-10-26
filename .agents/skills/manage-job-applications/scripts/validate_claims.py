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


def validate_claims(ledger: Any, profile: Any, application: Any) -> None:
    validate_against_schema(
        ledger, "claim-ledger.schema.json", "claim ledger"
    )
    data = require_object(ledger, "claim ledger")
    profile_data = require_object(profile, "profile")
    application_data = require_object(application, "application")
    if data["candidate_id"] != profile_data.get("candidate_id"):
        raise ValidationError(
            "claim ledger candidate_id does not match profile"
        )
    if data["application_id"] != application_data.get("application_id"):
        raise ValidationError(
            "claim ledger application_id does not match application"
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
    covered_fact_ids: set[str] = set()
    for index, raw_claim in enumerate(
        require_list(data["claims"], "claim ledger.claims")
    ):
        label = f"claim ledger.claims[{index}]"
        claim = require_object(raw_claim, label)
        claim_id = require_string(claim["claim_id"], f"{label}.claim_id")
        if claim_id in claim_ids:
            raise ValidationError(f"{label}.claim_id is duplicated")
        claim_ids.add(claim_id)
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
            covered_fact_ids.add(evidence_id)
    required_fact_ids = {
        fact_id
        for artifact in artifacts.values()
        for fact_id in unique_strings(
            artifact.get("source_fact_ids"), "artifact.source_fact_ids"
        )
    }
    missing = sorted(required_fact_ids - covered_fact_ids)
    if missing:
        raise ValidationError(
            "claim ledger does not cover artifact source facts: "
            + ", ".join(missing)
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
    args = parser.parse_args()
    try:
        validate_claims(
            load_json(args.ledger),
            load_json(args.profile),
            load_json(args.application),
        )
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
