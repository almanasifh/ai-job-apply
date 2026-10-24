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


def validate_answers(answers: Any) -> None:
    validate_against_schema(answers, "answers.schema.json", "answers")
    data = require_object(answers, "answers")
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
        if status == "VERIFIED":
            if answer["answer"] is None:
                raise ValidationError(f"{label}.answer is required when VERIFIED")
            if not evidence_ids:
                raise ValidationError(f"{label}.evidence_ids is required when VERIFIED")
            parse_datetime(answer["reviewed_at"], f"{label}.reviewed_at")
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
    args = parser.parse_args()
    try:
        validate_answers(load_json(args.answers))
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.answers}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
