from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import (
    ValidationError,
    load_json,
    parse_datetime,
    require_list,
    require_object,
    require_string,
    unique_strings,
    validate_against_schema,
)
from validate_profile import validate_profile


def _reject_float_answer(value: Any, label: str) -> None:
    if isinstance(value, float):
        raise ValidationError(
            f"{label}.answer uses a float; encode exact values as strings or integers"
        )


def validate_answers(answers: Any, profile: Any | None = None) -> None:
    validate_against_schema(answers, "answers.schema.json", "answers")
    data = require_object(answers, "answers")
    profile_facts: dict[str, Any] | None = None
    if profile is not None:
        validate_profile(profile)
        profile_data = require_object(profile, "profile")
        if data["candidate_id"] != profile_data["candidate_id"]:
            raise ValidationError("answers.candidate_id does not match the profile")
        profile_facts = {
            require_string(item["id"], f"profile fact {index}.id"): item
            for index, item in enumerate(require_list(profile_data["facts"], "profile.facts"))
        }
    question_keys: set[str] = set()
    for index, raw_answer in enumerate(require_list(data["answers"], "answers.answers")):
        label = f"answers.answers[{index}]"
        answer = require_object(raw_answer, label)
        question_key = require_string(answer["question_key"], f"{label}.question_key")
        if question_key in question_keys:
            raise ValidationError(f"{label}.question_key is duplicated")
        question_keys.add(question_key)
        evidence_ids = unique_strings(answer["evidence_ids"], f"{label}.evidence_ids")
        status = answer["status"]
        _reject_float_answer(answer["answer"], label)
        if profile_facts is not None:
            missing = sorted(set(evidence_ids) - profile_facts.keys())
            if missing:
                raise ValidationError(
                    f"{label}.evidence_ids is unknown: {', '.join(missing)}"
                )
        if status == "VERIFIED":
            if answer["answer"] is None:
                raise ValidationError(f"{label}.answer is required when VERIFIED")
            if not evidence_ids:
                raise ValidationError(f"{label}.evidence_ids is required when VERIFIED")
            parse_datetime(answer["reviewed_at"], f"{label}.reviewed_at")
            if profile_facts is not None:
                unverified = sorted(
                    evidence_id
                    for evidence_id in evidence_ids
                    if profile_facts[evidence_id]["status"] != "VERIFIED"
                )
                if unverified:
                    raise ValidationError(
                        f"{label}.evidence_ids is not VERIFIED: {', '.join(unverified)}"
                    )
        elif status == "UNKNOWN":
            if answer["answer"] is not None or evidence_ids or answer["reviewed_at"] is not None:
                raise ValidationError(f"{label} must not claim an answer, evidence, or review time while UNKNOWN")
        else:
            if answer["answer"] is not None:
                raise ValidationError(f"{label}.answer must be null while CONFLICTING")
            if not evidence_ids:
                raise ValidationError(f"{label}.evidence_ids is required while CONFLICTING")
            parse_datetime(answer["reviewed_at"], f"{label}.reviewed_at")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a scoped candidate answer library.")
    parser.add_argument("answers", type=Path)
    parser.add_argument(
        "--profile",
        type=Path,
        help="Optional profile used to resolve answer evidence_ids",
    )
    args = parser.parse_args()
    try:
        profile = load_json(args.profile) if args.profile else None
        validate_answers(load_json(args.answers), profile)
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.answers}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
