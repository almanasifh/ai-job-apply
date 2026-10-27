from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = REPO_ROOT / "evals" / "behavioral-scenarios.json"
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "manage-job-applications"
WORKFLOW_STATUSES = {
    "RESEARCHED", "ROUTED", "PREPARING", "READY", "NEEDS_INPUT",
    "NEEDS_VERIFICATION", "TECHNICAL_HOLD", "SUBMISSION_UNCERTAIN",
    "SENT", "SUBMITTED", "DELIVERY_FAILED", "SUBMISSION_FAILED", "SKIPPED",
}
CAPABILITIES = {"READ_INPUT", "READ_FILES", "WRITE_FILES", "BROWSER", "EMAIL", "PROVIDER_ACTION", "DELEGATE"}
REQUIRED_RISK_TAGS = {
    "source_freshness", "mandatory_gap", "truthfulness", "tool_absence",
    "approval_binding", "uncertain_result", "prompt_injection", "duplicate",
    "batch_limit", "language", "employer_exclusion", "shortlist_authority",
    "approval_expiry", "approval_timing", "required_answer",
    "security_challenge", "outcome_separation", "artifact_qa",
    "delegation_privacy", "delegation_authority", "late_result",
    "delegated_claim", "delegated_outcome", "native_spawn",
    "sequential_fallback", "delegation_dedup", "output_conflict",
    "delegation_capacity", "release_privacy",
}
SCENARIO_FIELDS = {
    "id", "title", "prompt", "available_capabilities", "fixture_refs",
    "reference_files", "risk_tags", "expected_status", "expected_behaviors",
    "forbidden_behaviors", "evidence_scope",
}
EVIDENCE_SCOPES = {
    "skill_runtime",
    "host_capability",
    "release_packaging",
}


class EvaluationError(ValueError):
    pass


def _strings(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise EvaluationError(f"{label} must be a{' non-empty' if not allow_empty else ''} string array")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise EvaluationError(f"{label}[{index}] must be a non-empty string")
        result.append(item)
    if len(result) != len(set(result)):
        raise EvaluationError(f"{label} must contain unique values")
    return result


def _resolve_within(root: Path, value: str, label: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        raise EvaluationError(f"{label} must be relative")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    if resolved_root != resolved and resolved_root not in resolved.parents:
        raise EvaluationError(f"{label} escapes its allowed root")
    return resolved


def validate_catalog(catalog: Any, *, repo_root: Path = REPO_ROOT) -> None:
    if not isinstance(catalog, dict) or set(catalog) != {"schema_version", "skill_name", "scenarios"}:
        raise EvaluationError("catalog must contain only schema_version, skill_name, and scenarios")
    if catalog["schema_version"] != "1.0" or catalog["skill_name"] != "manage-job-applications":
        raise EvaluationError("catalog identity is invalid")
    scenarios = catalog["scenarios"]
    if not isinstance(scenarios, list) or len(scenarios) < 8:
        raise EvaluationError("catalog must contain at least eight scenarios")

    scenario_ids: set[str] = set()
    observed_risks: set[str] = set()
    for index, scenario in enumerate(scenarios):
        label = f"scenarios[{index}]"
        if not isinstance(scenario, dict) or set(scenario) != SCENARIO_FIELDS:
            raise EvaluationError(f"{label} has missing or unsupported fields")
        scenario_id = scenario["id"]
        if not isinstance(scenario_id, str) or not re.fullmatch(r"eval_[a-z0-9-]+", scenario_id):
            raise EvaluationError(f"{label}.id must match eval_[a-z0-9-]+")
        if scenario_id in scenario_ids:
            raise EvaluationError(f"{label}.id is duplicated")
        scenario_ids.add(scenario_id)
        for field in ("title", "prompt"):
            if not isinstance(scenario[field], str) or not scenario[field].strip():
                raise EvaluationError(f"{label}.{field} must be a non-empty string")

        capabilities = set(_strings(scenario["available_capabilities"], f"{label}.available_capabilities"))
        if capabilities - CAPABILITIES:
            raise EvaluationError(f"{label}.available_capabilities contains an unknown capability")
        risks = set(_strings(scenario["risk_tags"], f"{label}.risk_tags"))
        if risks - REQUIRED_RISK_TAGS:
            raise EvaluationError(f"{label}.risk_tags contains an unknown tag")
        observed_risks.update(risks)
        status = scenario["expected_status"]
        if status not in WORKFLOW_STATUSES:
            raise EvaluationError(f"{label}.expected_status is not canonical")
        evidence_scope = scenario["evidence_scope"]
        if evidence_scope not in EVIDENCE_SCOPES:
            raise EvaluationError(f"{label}.evidence_scope is not supported")
        _strings(scenario["expected_behaviors"], f"{label}.expected_behaviors")
        _strings(scenario["forbidden_behaviors"], f"{label}.forbidden_behaviors")

        for fixture_index, fixture in enumerate(_strings(scenario["fixture_refs"], f"{label}.fixture_refs", allow_empty=True)):
            path = _resolve_within(repo_root, fixture, f"{label}.fixture_refs[{fixture_index}]")
            if not path.is_file():
                raise EvaluationError(f"{label}.fixture_refs[{fixture_index}] does not exist")
        for reference_index, reference in enumerate(_strings(scenario["reference_files"], f"{label}.reference_files")):
            path = _resolve_within(SKILL_ROOT, reference, f"{label}.reference_files[{reference_index}]")
            if not path.is_file():
                raise EvaluationError(f"{label}.reference_files[{reference_index}] does not exist")

    missing_risks = sorted(REQUIRED_RISK_TAGS - observed_risks)
    if missing_risks:
        raise EvaluationError(f"catalog is missing risk coverage: {', '.join(missing_risks)}")


def load_catalog(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"Cannot read evaluation catalog {path}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate fictional skill behavior scenarios.")
    parser.add_argument("catalog", nargs="?", type=Path, default=DEFAULT_CATALOG)
    args = parser.parse_args()
    try:
        validate_catalog(load_catalog(args.catalog))
    except EvaluationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.catalog}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
