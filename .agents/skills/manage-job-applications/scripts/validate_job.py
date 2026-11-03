from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from common import (
    ValidationError,
    canonical_digest,
    load_json,
    parse_datetime,
    require_list,
    require_object,
    require_sha256,
    require_string,
    validate_against_schema,
)


ACTION_FRESHNESS = timedelta(hours=24)


def validate_job(job: Any, *, at: datetime | None = None) -> None:
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
    require_sha256(data["content_digest"], "job.content_digest")
    expected_digest = canonical_digest(data, omit={"content_digest"})
    if data["content_digest"] != expected_digest:
        raise ValidationError("job.content_digest does not match canonical content")
    if at is not None:
        if data["availability"] != "OPEN":
            raise ValidationError("job.availability must be OPEN at action time")
        if at - checked_at > ACTION_FRESHNESS:
            raise ValidationError("job.checked_at is older than 24 hours at action time")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a captured vacancy contract.")
    parser.add_argument("job", type=Path)
    parser.add_argument(
        "--at",
        help="ISO 8601 action time; when set, require an OPEN vacancy checked within 24 hours",
    )
    args = parser.parse_args()
    try:
        action_time = parse_datetime(args.at, "--at") if args.at else None
        validate_job(load_json(args.job), at=action_time)
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.job}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
