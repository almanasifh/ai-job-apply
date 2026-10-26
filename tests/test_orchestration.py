from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "manage-job-applications"
ASSETS = SKILL_ROOT / "assets" / "fictional-profile-pack"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from common import ValidationError, canonical_digest, load_json, parse_datetime
from validate_claims import validate_claims
from validate_orchestration import validate_delegation, validate_result


class OrchestrationTests(unittest.TestCase):
    def test_fictional_delegation_and_result_are_valid(self) -> None:
        delegation = validate_delegation(
            load_json(ASSETS / "delegation.json"),
            parse_datetime("2099-01-01T00:05:00Z", "test time"),
        )
        validate_result(
            load_json(ASSETS / "specialist-result.json"),
            delegation,
            parse_datetime("2099-01-01T00:05:00Z", "test time"),
        )

    def test_scout_cannot_receive_candidate_facts(self) -> None:
        delegation = load_json(ASSETS / "delegation.json")
        delegation["role"] = "SCOUT"
        delegation["capabilities"] = ["READ_PUBLIC"]
        delegation["task_digest"] = canonical_digest(
            delegation, omit={"task_digest"}
        )
        with self.assertRaisesRegex(
            ValidationError, "cannot receive candidate fact"
        ):
            validate_delegation(
                delegation,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_role_cannot_expand_capabilities(self) -> None:
        delegation = load_json(ASSETS / "delegation.json")
        delegation["capabilities"].append("DRAFT_CONTENT")
        delegation["task_digest"] = canonical_digest(
            delegation, omit={"task_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "exactly match"):
            validate_delegation(
                delegation,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_delegation_requires_bound_input(self) -> None:
        delegation = load_json(ASSETS / "delegation.json")
        delegation["input_refs"] = []
        delegation["input_digests"] = []
        delegation["task_digest"] = canonical_digest(
            delegation, omit={"task_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "at least (?:one input|1 item)"):
            validate_delegation(
                delegation,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_result_must_match_delegated_role(self) -> None:
        delegation = validate_delegation(
            load_json(ASSETS / "delegation.json"),
            parse_datetime("2099-01-01T00:05:00Z", "test time"),
        )
        result = load_json(ASSETS / "specialist-result.json")
        result["role"] = "DRAFTER"
        result["result_digest"] = canonical_digest(
            result, omit={"result_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "different delegation"):
            validate_result(
                result,
                delegation,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_result_must_match_delegated_task(self) -> None:
        delegation = validate_delegation(
            load_json(ASSETS / "delegation.json"),
            parse_datetime("2099-01-01T00:05:00Z", "test time"),
        )
        result = load_json(ASSETS / "specialist-result.json")
        result["task_digest"] = "0" * 64
        result["result_digest"] = canonical_digest(
            result, omit={"result_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "different delegation task"):
            validate_result(
                result,
                delegation,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_result_must_finish_within_delegation_window(self) -> None:
        delegation = validate_delegation(
            load_json(ASSETS / "delegation.json"),
            parse_datetime("2099-01-01T00:05:00Z", "test time"),
        )
        result = load_json(ASSETS / "specialist-result.json")
        result["completed_at"] = delegation["expires_at"]
        result["result_digest"] = canonical_digest(
            result, omit={"result_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "validity window"):
            validate_result(
                result,
                delegation,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_result_cannot_cite_unpermitted_candidate_fact(self) -> None:
        delegation = validate_delegation(
            load_json(ASSETS / "delegation.json"),
            parse_datetime("2099-01-01T00:05:00Z", "test time"),
        )
        result = load_json(ASSETS / "specialist-result.json")
        result["evidence_ids"].append("fact_not-delegated")
        result["result_digest"] = canonical_digest(
            result, omit={"result_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "exceeds permitted"):
            validate_result(
                result,
                delegation,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_failed_result_cannot_return_consumable_output(self) -> None:
        delegation = validate_delegation(
            load_json(ASSETS / "delegation.json"),
            parse_datetime("2099-01-01T00:05:00Z", "test time"),
        )
        result = load_json(ASSETS / "specialist-result.json")
        result["status"] = "FAILED"
        result["result_digest"] = canonical_digest(
            result, omit={"result_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "cannot provide outputs"):
            validate_result(
                result,
                delegation,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_claim_ledger_is_bound_to_verified_permitted_facts(self) -> None:
        validate_claims(
            load_json(ASSETS / "claim-ledger.json"),
            load_json(ASSETS / "profile.json"),
            load_json(ASSETS / "application.json"),
            ASSETS,
        )

    def test_claim_cannot_use_fact_outside_allowed_use(self) -> None:
        ledger = copy.deepcopy(load_json(ASSETS / "claim-ledger.json"))
        ledger["claims"][0]["use"] = "CONTACT"
        ledger["ledger_digest"] = canonical_digest(
            ledger, omit={"ledger_digest"}
        )
        with self.assertRaisesRegex(
            ValidationError, "outside its allowed uses"
        ):
            validate_claims(
                ledger,
                load_json(ASSETS / "profile.json"),
                load_json(ASSETS / "application.json"),
                ASSETS,
            )

    def test_claim_ledger_must_bind_exact_application_package(self) -> None:
        ledger = load_json(ASSETS / "claim-ledger.json")
        ledger["application_digest"] = "0" * 64
        ledger["ledger_digest"] = canonical_digest(
            ledger, omit={"ledger_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "exact application package"):
            validate_claims(
                ledger,
                load_json(ASSETS / "profile.json"),
                load_json(ASSETS / "application.json"),
                ASSETS,
            )

    def test_claim_evidence_must_match_each_artifact_fact_set(self) -> None:
        application = load_json(ASSETS / "application.json")
        application["artifacts"][0]["source_fact_ids"] = [
            "fact_support-years"
        ]
        application["payload_digest"] = canonical_digest(
            application, omit={"payload_digest"}
        )
        ledger = load_json(ASSETS / "claim-ledger.json")
        ledger["application_digest"] = application["payload_digest"]
        ledger["ledger_digest"] = canonical_digest(
            ledger, omit={"ledger_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "not declared by artifact"):
            validate_claims(
                ledger,
                load_json(ASSETS / "profile.json"),
                application,
                ASSETS,
            )


if __name__ == "__main__":
    unittest.main()
