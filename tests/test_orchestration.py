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
from validate_orchestration import (
    validate_delegation,
    validate_delegation_set,
    validate_result,
    validate_result_set,
)


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
        delegation["input_kinds"] = ["PUBLIC_VACANCY", "PUBLIC_VACANCY"]
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

    def test_scout_cannot_receive_a_minimized_facts_input(self) -> None:
        delegation = load_json(ASSETS / "delegation.json")
        delegation["role"] = "SCOUT"
        delegation["capabilities"] = ["READ_PUBLIC"]
        delegation["permitted_fact_ids"] = []
        delegation["task_digest"] = canonical_digest(
            delegation, omit={"task_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "PUBLIC_VACANCY"):
            validate_delegation(
                delegation,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_matcher_requires_public_vacancy_and_minimized_facts(self) -> None:
        delegation = load_json(ASSETS / "delegation.json")
        delegation["input_refs"] = delegation["input_refs"][:1]
        delegation["input_kinds"] = ["PUBLIC_VACANCY"]
        delegation["input_digests"] = delegation["input_digests"][:1]
        delegation["task_digest"] = canonical_digest(
            delegation, omit={"task_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "MINIMIZED_FACTS"):
            validate_delegation(
                delegation,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_scout_application_id_must_be_null(self) -> None:
        delegation = load_json(ASSETS / "delegation.json")
        delegation["role"] = "SCOUT"
        delegation["capabilities"] = ["READ_PUBLIC"]
        delegation["input_refs"] = delegation["input_refs"][:1]
        delegation["input_kinds"] = ["PUBLIC_VACANCY"]
        delegation["input_digests"] = delegation["input_digests"][:1]
        delegation["permitted_fact_ids"] = []
        delegation["task_digest"] = canonical_digest(
            delegation, omit={"task_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "must be null"):
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

    def test_completed_result_can_be_reviewed_after_lease_expiry(self) -> None:
        delegation = validate_delegation(
            load_json(ASSETS / "delegation.json"),
            parse_datetime("2099-01-01T00:16:00Z", "test time"),
            require_active=False,
        )
        validate_result(
            load_json(ASSETS / "specialist-result.json"),
            delegation,
            parse_datetime("2099-01-01T00:16:00Z", "test time"),
        )

    def test_result_cannot_claim_external_action(self) -> None:
        delegation = validate_delegation(
            load_json(ASSETS / "delegation.json"),
            parse_datetime("2099-01-01T00:05:00Z", "test time"),
        )
        result = load_json(ASSETS / "specialist-result.json")
        result["external_action_taken"] = True
        result["result_digest"] = canonical_digest(
            result, omit={"result_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "external_action_taken"):
            validate_result(
                result,
                delegation,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_result_attempt_must_match_delegation(self) -> None:
        delegation = validate_delegation(
            load_json(ASSETS / "delegation.json"),
            parse_datetime("2099-01-01T00:05:00Z", "test time"),
        )
        result = load_json(ASSETS / "specialist-result.json")
        result["attempt_id"] = "attempt_example-match-101-02"
        result["result_digest"] = canonical_digest(
            result, omit={"result_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "different delegation"):
            validate_result(
                result,
                delegation,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_timed_out_result_is_non_consumable_and_explained(self) -> None:
        delegation = validate_delegation(
            load_json(ASSETS / "delegation.json"),
            parse_datetime("2099-01-01T00:05:00Z", "test time"),
        )
        result = load_json(ASSETS / "specialist-result.json")
        result["status"] = "TIMED_OUT"
        result["output_refs"] = []
        result["output_digests"] = []
        result["evidence_ids"] = []
        result["unresolved"] = ["worker exceeded the bounded lease"]
        result["result_digest"] = canonical_digest(
            result, omit={"result_digest"}
        )
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

    def test_delegation_set_cannot_exceed_nineteen_concurrent_specialists(self) -> None:
        source = load_json(ASSETS / "delegation.json")
        delegations = []
        for index in range(20):
            delegation = copy.deepcopy(source)
            delegation["task_id"] = f"task_example-match-{index:03d}"
            delegation["attempt_id"] = f"attempt_example-match-{index:03d}-01"
            delegation["input_refs"][0] = f"job_example-support-{index:03d}"
            delegation["task_digest"] = canonical_digest(
                delegation, omit={"task_digest"}
            )
            delegations.append(delegation)
        with self.assertRaisesRegex(ValidationError, "19 concurrent specialist"):
            validate_delegation_set(
                delegations,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_delegation_set_allows_more_than_nineteen_tasks_in_waves(self) -> None:
        source = load_json(ASSETS / "delegation.json")
        delegations = []
        for index in range(20):
            delegation = copy.deepcopy(source)
            delegation["task_id"] = f"task_example-wave-{index:03d}"
            delegation["attempt_id"] = f"attempt_example-wave-{index:03d}-01"
            delegation["issued_at"] = f"2099-01-01T{index:02d}:00:00Z"
            delegation["expires_at"] = f"2099-01-01T{index:02d}:15:00Z"
            delegation["task_digest"] = canonical_digest(
                delegation, omit={"task_digest"}
            )
            delegations.append(delegation)
        validate_delegation_set(
            delegations,
            parse_datetime("2099-01-02T00:00:00Z", "test time"),
            require_active=False,
        )

    def test_delegation_set_rejects_duplicate_tasks(self) -> None:
        delegation = load_json(ASSETS / "delegation.json")
        with self.assertRaisesRegex(ValidationError, "duplicate attempt"):
            validate_delegation_set(
                [delegation, copy.deepcopy(delegation)],
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_delegation_set_rejects_overlapping_retry_of_same_task(self) -> None:
        first = load_json(ASSETS / "delegation.json")
        retry = copy.deepcopy(first)
        retry["attempt_id"] = "attempt_example-match-101-02"
        retry["expires_at"] = "2099-01-01T00:20:00Z"
        retry["task_digest"] = canonical_digest(
            retry, omit={"task_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "overlapping attempts"):
            validate_delegation_set(
                [first, retry],
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_delegation_set_allows_sequential_retry_attempt(self) -> None:
        first = load_json(ASSETS / "delegation.json")
        retry = copy.deepcopy(first)
        retry["attempt_id"] = "attempt_example-match-101-02"
        retry["issued_at"] = "2099-01-01T00:15:00Z"
        retry["expires_at"] = "2099-01-01T00:30:00Z"
        retry["task_digest"] = canonical_digest(
            retry, omit={"task_digest"}
        )
        validate_delegation_set(
            [first, retry],
            parse_datetime("2099-01-01T00:31:00Z", "test time"),
            require_active=False,
        )

    def test_result_set_rejects_shared_output_ownership(self) -> None:
        first_delegation = load_json(ASSETS / "delegation.json")
        first_result = load_json(ASSETS / "specialist-result.json")
        second_delegation = copy.deepcopy(first_delegation)
        second_delegation["task_id"] = "task_example-match-102"
        second_delegation["attempt_id"] = "attempt_example-match-102-01"
        second_delegation["input_refs"][0] = "job_example-support-102"
        second_delegation["task_digest"] = canonical_digest(
            second_delegation, omit={"task_digest"}
        )
        second_result = copy.deepcopy(first_result)
        second_result["task_id"] = second_delegation["task_id"]
        second_result["attempt_id"] = second_delegation["attempt_id"]
        second_result["task_digest"] = second_delegation["task_digest"]
        second_result["result_digest"] = canonical_digest(
            second_result, omit={"result_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "same output reference"):
            validate_result_set(
                [
                    (first_delegation, first_result),
                    (second_delegation, second_result),
                ],
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_cancelled_attempt_can_be_retried_without_consuming_output(self) -> None:
        first_delegation = load_json(ASSETS / "delegation.json")
        first_result = load_json(ASSETS / "specialist-result.json")
        first_result["status"] = "CANCELLED"
        first_result["completed_at"] = "2099-01-01T00:14:00Z"
        first_result["output_refs"] = []
        first_result["output_digests"] = []
        first_result["evidence_ids"] = []
        first_result["unresolved"] = ["coordinator cancelled the first attempt"]
        first_result["result_digest"] = canonical_digest(
            first_result, omit={"result_digest"}
        )

        retry_delegation = copy.deepcopy(first_delegation)
        retry_delegation["attempt_id"] = "attempt_example-match-101-02"
        retry_delegation["issued_at"] = "2099-01-01T00:15:00Z"
        retry_delegation["expires_at"] = "2099-01-01T00:30:00Z"
        retry_delegation["task_digest"] = canonical_digest(
            retry_delegation, omit={"task_digest"}
        )
        retry_result = load_json(ASSETS / "specialist-result.json")
        retry_result["attempt_id"] = retry_delegation["attempt_id"]
        retry_result["task_digest"] = retry_delegation["task_digest"]
        retry_result["started_at"] = "2099-01-01T00:16:00Z"
        retry_result["completed_at"] = "2099-01-01T00:17:00Z"
        retry_result["result_digest"] = canonical_digest(
            retry_result, omit={"result_digest"}
        )
        validate_result_set(
            [
                (first_delegation, first_result),
                (retry_delegation, retry_result),
            ],
            parse_datetime("2099-01-01T00:31:00Z", "test time"),
        )

    def test_completed_task_cannot_be_retried(self) -> None:
        first_delegation = load_json(ASSETS / "delegation.json")
        first_result = load_json(ASSETS / "specialist-result.json")
        retry_delegation = copy.deepcopy(first_delegation)
        retry_delegation["attempt_id"] = "attempt_example-match-101-02"
        retry_delegation["issued_at"] = "2099-01-01T00:15:00Z"
        retry_delegation["expires_at"] = "2099-01-01T00:30:00Z"
        retry_delegation["task_digest"] = canonical_digest(
            retry_delegation, omit={"task_digest"}
        )
        retry_result = copy.deepcopy(first_result)
        retry_result["attempt_id"] = retry_delegation["attempt_id"]
        retry_result["task_digest"] = retry_delegation["task_digest"]
        retry_result["status"] = "FAILED"
        retry_result["started_at"] = "2099-01-01T00:16:00Z"
        retry_result["completed_at"] = "2099-01-01T00:17:00Z"
        retry_result["output_refs"] = []
        retry_result["output_digests"] = []
        retry_result["evidence_ids"] = []
        retry_result["unresolved"] = ["retry must not proceed after completion"]
        retry_result["result_digest"] = canonical_digest(
            retry_result, omit={"result_digest"}
        )
        with self.assertRaisesRegex(ValidationError, "retry after a completed"):
            validate_result_set(
                [
                    (first_delegation, first_result),
                    (retry_delegation, retry_result),
                ],
                parse_datetime("2099-01-01T00:31:00Z", "test time"),
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
