from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import (
    ValidationError,
    load_json,
    require_list,
    require_object,
    require_string,
    unique_strings,
    validate_against_schema,
)
from validate_job import validate_job
from validate_profile import validate_profile


def validate_match(match: Any, job: Any, profile: Any) -> None:
    validate_against_schema(match, "match.schema.json", "match")
    validate_job(job)
    validate_profile(profile)
    data = require_object(match, "match")
    job_data = require_object(job, "job")
    profile_data = require_object(profile, "profile")
    if data["candidate_id"] != profile_data["candidate_id"]:
        raise ValidationError("match.candidate_id does not match the profile")
    if data["job_id"] != job_data["job_id"]:
        raise ValidationError("match.job_id does not match the vacancy")

    job_requirements = {
        require_string(item["id"], f"job requirement {index}.id"): item
        for index, item in enumerate(require_list(job_data["requirements"], "job.requirements"))
    }
    profile_facts = {
        require_string(item["id"], f"profile fact {index}.id"): item
        for index, item in enumerate(require_list(profile_data["facts"], "profile.facts"))
    }
    mapped_ids: set[str] = set()
    mapped_states: dict[str, str] = {}
    for index, raw_mapping in enumerate(require_list(data["requirements"], "match.requirements")):
        label = f"match.requirements[{index}]"
        mapping = require_object(raw_mapping, label)
        requirement_id = require_string(mapping["requirement_id"], f"{label}.requirement_id")
        if requirement_id not in job_requirements:
            raise ValidationError(f"{label}.requirement_id is not present in the vacancy")
        if requirement_id in mapped_ids:
            raise ValidationError(f"{label}.requirement_id is duplicated")
        mapped_ids.add(requirement_id)
        state = mapping["state"]
        mapped_states[requirement_id] = state
        evidence_ids = unique_strings(mapping["evidence_ids"], f"{label}.evidence_ids")
        missing_evidence = sorted(set(evidence_ids) - profile_facts.keys())
        if missing_evidence:
            raise ValidationError(f"{label}.evidence_ids is unknown: {', '.join(missing_evidence)}")
        unverified = sorted(
            evidence_id
            for evidence_id in evidence_ids
            if profile_facts[evidence_id]["status"] != "VERIFIED"
        )
        if unverified:
            raise ValidationError(f"{label}.evidence_ids is not VERIFIED: {', '.join(unverified)}")
        if state in {"SUPPORTED", "PARTIAL"} and not evidence_ids:
            raise ValidationError(f"{label}.evidence_ids is required for {state}")
        if state == "UNKNOWN" and evidence_ids:
            raise ValidationError(f"{label}.evidence_ids must be empty for UNKNOWN")
        if state == "NOT_APPLICABLE" and not mapping["note"].strip():
            raise ValidationError(f"{label}.note is required for NOT_APPLICABLE")

    missing_requirements = sorted(job_requirements.keys() - mapped_ids)
    if missing_requirements:
        raise ValidationError(f"match is missing requirements: {', '.join(missing_requirements)}")
    if data["decision"] == "PROCEED":
        blocking = sorted(
            requirement_id
            for requirement_id, requirement in job_requirements.items()
            if requirement["kind"] == "MANDATORY" and mapped_states[requirement_id] in {"GAP", "UNKNOWN"}
        )
        if blocking:
            raise ValidationError(f"match.decision cannot be PROCEED with unresolved mandatory requirements: {', '.join(blocking)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate requirement evidence mapping against a vacancy and profile.")
    parser.add_argument("match", type=Path)
    parser.add_argument("job", type=Path)
    parser.add_argument("profile", type=Path)
    args = parser.parse_args()
    try:
        validate_match(load_json(args.match), load_json(args.job), load_json(args.profile))
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.match} + {args.job} + {args.profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
