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
            load_json(ASSETS / "specialist-result.json"), delegation
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
            validate_result(result, delegation)

    def test_claim_ledger_is_bound_to_verified_permitted_facts(self) -> None:
        validate_claims(
            load_json(ASSETS / "claim-ledger.json"),
            load_json(ASSETS / "profile.json"),
            load_json(ASSETS / "application.json"),
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
            )


if __name__ == "__main__":
    unittest.main()
