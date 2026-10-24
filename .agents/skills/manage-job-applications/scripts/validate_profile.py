from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import (
    ValidationError,
    load_json,
    parse_datetime,
    reject_extra_keys,
    require_enum,
    require_keys,
    require_list,
    require_object,
    require_string,
    unique_strings,
    validate_against_schema,
)


FACT_STATUSES = {"VERIFIED", "UNKNOWN", "CONFLICTING"}
ALLOWED_USES = {"CV", "COVER_LETTER", "SCREENING", "CONTACT"}
CHANNELS = {"EMAIL", "PORTAL", "LINKEDIN", "MANUAL"}


def validate_profile(profile: Any) -> None:
    validate_against_schema(profile, "profile.schema.json", "profile")
    data = require_object(profile, "profile")
    fields = {"schema_version", "candidate_id", "display_name", "facts", "preferences", "exclusions"}
    require_keys(data, fields, "profile")
    reject_extra_keys(data, fields, "profile")
    if data["schema_version"] != "1.0":
        raise ValidationError("profile.schema_version must be 1.0")
    candidate_id = require_string(data["candidate_id"], "profile.candidate_id")
    if not candidate_id.startswith("cand_"):
        raise ValidationError("profile.candidate_id must start with cand_")
    require_string(data["display_name"], "profile.display_name")

    fact_ids: set[str] = set()
    fact_keys: set[str] = set()
    for index, raw_fact in enumerate(require_list(data["facts"], "profile.facts")):
        label = f"profile.facts[{index}]"
        fact = require_object(raw_fact, label)
        fact_fields = {"id", "key", "value", "status", "source", "verified_at", "allowed_uses"}
        require_keys(fact, fact_fields, label)
        reject_extra_keys(fact, fact_fields, label)
        fact_id = require_string(fact["id"], f"{label}.id")
        fact_key = require_string(fact["key"], f"{label}.key")
        if not fact_id.startswith("fact_"):
            raise ValidationError(f"{label}.id must start with fact_")
        if fact_id in fact_ids or fact_key in fact_keys:
            raise ValidationError(f"{label} duplicates a fact id or key")
        fact_ids.add(fact_id)
        fact_keys.add(fact_key)
        status = require_enum(fact["status"], FACT_STATUSES, f"{label}.status")
        source = require_string(fact["source"], f"{label}.source")
        uses = unique_strings(fact["allowed_uses"], f"{label}.allowed_uses")
        if set(uses) - ALLOWED_USES:
            raise ValidationError(f"{label}.allowed_uses contains an unsupported use")
        if status == "VERIFIED":
            if not source:
                raise ValidationError(f"{label}.source is required for verified facts")
            parse_datetime(fact["verified_at"], f"{label}.verified_at")
        elif status == "UNKNOWN":
            if fact["value"] is not None or fact["verified_at"] is not None:
                raise ValidationError(f"{label} must not claim a value or verification time while UNKNOWN")
        elif fact["verified_at"] is not None:
            parse_datetime(fact["verified_at"], f"{label}.verified_at")

    preferences = require_object(data["preferences"], "profile.preferences")
    preference_fields = {"target_roles", "locations", "channels"}
    require_keys(preferences, preference_fields, "profile.preferences")
    reject_extra_keys(preferences, preference_fields, "profile.preferences")
    unique_strings(preferences["target_roles"], "profile.preferences.target_roles")
    unique_strings(preferences["locations"], "profile.preferences.locations")
    channels = unique_strings(preferences["channels"], "profile.preferences.channels")
    if set(channels) - CHANNELS:
        raise ValidationError("profile.preferences.channels contains an unsupported channel")
    unique_strings(data["exclusions"], "profile.exclusions")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a candidate profile contract.")
    parser.add_argument("profile", type=Path)
    args = parser.parse_args()
    try:
        validate_profile(load_json(args.profile))
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
