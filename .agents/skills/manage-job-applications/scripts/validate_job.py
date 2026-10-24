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
    validate_against_schema,
)


def validate_job(job: Any) -> None:
    validate_against_schema(job, "job.schema.json", "job")
    data = require_object(job, "job")
    captured_at = parse_datetime(data["captured_at"], "job.captured_at")
    checked_at = parse_datetime(data["checked_at"], "job.checked_at")
    if checked_at < captured_at:
        raise ValidationError("job.checked_at cannot be earlier than job.captured_at")
    requirement_ids: set[str] = set()
    for index, raw_requirement in enumerate(require_list(data["requirements"], "job.requirements")):
        label = f"job.requirements[{index}]"
        requirement = require_object(raw_requirement, label)
        requirement_id = require_string(requirement["id"], f"{label}.id")
        if requirement_id in requirement_ids:
            raise ValidationError(f"{label}.id is duplicated")
        requirement_ids.add(requirement_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a captured vacancy contract.")
    parser.add_argument("job", type=Path)
    args = parser.parse_args()
    try:
        validate_job(load_json(args.job))
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.job}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
