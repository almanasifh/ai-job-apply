from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "manage-job-applications"
ASSETS = SKILL_ROOT / "assets" / "fictional-profile-pack"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import common
from common import ValidationError, canonical_digest, canonical_json_bytes, file_digest, load_json, parse_datetime, resolve_within
from validate_answers import validate_answers
from validate_application import validate_application, validate_authorization
from validate_checkpoint import load_events, validate_checkpoint
from validate_job import validate_job
from validate_match import validate_match
from validate_profile import validate_profile


class CanonicalJsonTests(unittest.TestCase):
    def test_canonical_json_is_utf8_and_key_sorted(self) -> None:
        self.assertEqual(canonical_json_bytes({"b": 1, "a": "é"}), '{"a":"é","b":1}'.encode("utf-8"))

    def test_floats_are_rejected_to_avoid_nonportable_hashes(self) -> None:
        with self.assertRaises(ValidationError):
            canonical_json_bytes({"value": 1.5})

    def test_duplicate_json_object_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"candidate_id":"first","candidate_id":"second"}', encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "duplicate key"):
                load_json(path)

    def test_schema_documents_are_cached_until_changed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            schema_root = Path(directory)
            schema_path = schema_root / "test.schema.json"
            schema_path.write_text('{"type":"string"}', encoding="utf-8")
            common._load_schema_cached.cache_clear()
            with mock.patch.object(common, "load_json", wraps=common.load_json) as loader:
                common.validate_against_schema("first", "test.schema.json", "value", schema_root=schema_root)
                common.validate_against_schema("second", "test.schema.json", "value", schema_root=schema_root)
            self.assertEqual(loader.call_count, 1)

    def test_file_digest_wraps_os_error_without_parent_path(self) -> None:
        source = Path("private-parent") / "artifact.pdf"
        with mock.patch.object(Path, "open", side_effect=PermissionError(13, "Permission denied", str(source))):
            with self.assertRaises(ValidationError) as raised:
                file_digest(source)
        self.assertIn("artifact.pdf", str(raised.exception))
        self.assertNotIn("private-parent", str(raised.exception))

    def test_load_json_wraps_os_error_without_parent_path(self) -> None:
        source = Path("private-parent") / "profile.json"
        with mock.patch.object(Path, "read_text", side_effect=PermissionError(13, "Permission denied", str(source))):
            with self.assertRaises(ValidationError) as raised:
                load_json(source)
        self.assertIn("profile.json", str(raised.exception))
        self.assertNotIn("private-parent", str(raised.exception))

    def test_resolve_within_rejects_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValidationError, "escapes its root"):
                resolve_within(Path(directory), "../outside.json")

    def test_resolve_within_hides_absolute_input(self) -> None:
        absolute = str(Path.cwd() / "private-parent" / "artifact.pdf")
        with self.assertRaises(ValidationError) as raised:
            resolve_within(Path.cwd(), absolute)
        self.assertNotIn("private-parent", str(raised.exception))

    def test_resolve_within_wraps_resolution_error(self) -> None:
        with mock.patch.object(Path, "resolve", side_effect=RuntimeError("private absolute path")):
            with self.assertRaisesRegex(ValidationError, "Cannot resolve artifact root") as raised:
                resolve_within("private-parent", "artifact.pdf")
        self.assertNotIn("private absolute path", str(raised.exception))


class ContractTests(unittest.TestCase):
    def test_fictional_profile_is_valid(self) -> None:
        validate_profile(load_json(ASSETS / "profile.json"))

    def test_private_profile_template_is_valid(self) -> None:
        template = SKILL_ROOT / "assets" / "templates" / "profile.template.json"
        validate_profile(load_json(template))

    def test_profile_identifier_must_match_schema_pattern(self) -> None:
        profile = load_json(ASSETS / "profile.json")
        profile["candidate_id"] = "cand_BAD!"
        with self.assertRaisesRegex(ValidationError, "pattern"):
            validate_profile(profile)

    def test_duplicate_profile_fact_is_rejected(self) -> None:
        profile = load_json(ASSETS / "profile.json")
        profile["facts"].append(copy.deepcopy(profile["facts"][0]))
        with self.assertRaises(ValidationError):
            validate_profile(profile)

    def test_unknown_profile_fact_cannot_claim_a_value(self) -> None:
        profile = load_json(SKILL_ROOT / "assets" / "templates" / "profile.template.json")
        profile["facts"][0]["value"] = "unsupported claim"
        with self.assertRaisesRegex(ValidationError, "while UNKNOWN"):
            validate_profile(profile)

    def test_application_and_exact_authorization_are_valid(self) -> None:
        validated = validate_application(load_json(ASSETS / "application.json"), ASSETS)
        validate_authorization(
            load_json(ASSETS / "authorization.json"),
            validated,
            parse_datetime("2099-01-01T00:05:00Z", "test time"),
        )

    def test_answer_library_job_and_match_are_valid(self) -> None:
        profile = load_json(ASSETS / "profile.json")
        job = load_json(ASSETS / "job.json")
        validate_answers(load_json(ASSETS / "answers.json"))
        validate_job(job)
        validate_match(load_json(ASSETS / "match.json"), job, profile)

    def test_application_answer_must_match_schema_type(self) -> None:
        application = load_json(ASSETS / "application.json")
        application["answers"][0]["answer"] = {"unsupported": "object"}
        application["payload_digest"] = canonical_digest(application, omit={"payload_digest"})
        with self.assertRaisesRegex(ValidationError, "JSON type"):
            validate_application(application, ASSETS)

    def test_failed_artifact_cannot_enter_immutable_package(self) -> None:
        application = load_json(ASSETS / "application.json")
        application["artifacts"][0]["qa_status"] = "FAILED"
        application["payload_digest"] = canonical_digest(application, omit={"payload_digest"})
        with mock.patch("validate_application.validate_against_schema"):
            with self.assertRaisesRegex(ValidationError, "PASSED"):
                validate_application(application, ASSETS)

    def test_material_application_change_invalidates_digest(self) -> None:
        application = load_json(ASSETS / "application.json")
        application["message"] += " Changed after approval."
        with self.assertRaisesRegex(ValidationError, "payload_digest"):
            validate_application(application, ASSETS)

    def test_changed_binding_is_not_authorized(self) -> None:
        application = load_json(ASSETS / "application.json")
        application["destination"] = "Different portal"
        application["payload_digest"] = canonical_digest(application, omit={"payload_digest"})
        validated = validate_application(application, ASSETS)
        with self.assertRaisesRegex(ValidationError, "matching immutable binding"):
            validate_authorization(
                load_json(ASSETS / "authorization.json"),
                validated,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_expired_authorization_is_rejected(self) -> None:
        validated = validate_application(load_json(ASSETS / "application.json"), ASSETS)
        with self.assertRaisesRegex(ValidationError, "expired"):
            validate_authorization(
                load_json(ASSETS / "authorization.json"),
                validated,
                parse_datetime("2099-01-01T00:16:00Z", "test time"),
            )

    def test_future_authorization_is_rejected(self) -> None:
        validated = validate_application(load_json(ASSETS / "application.json"), ASSETS)
        with self.assertRaisesRegex(ValidationError, "not active"):
            validate_authorization(
                load_json(ASSETS / "authorization.json"),
                validated,
                parse_datetime("2098-12-31T23:59:59Z", "test time"),
            )

    def test_batch_authorization_rejects_duplicate_targets(self) -> None:
        validated = validate_application(load_json(ASSETS / "application.json"), ASSETS)
        authorization = load_json(ASSETS / "authorization.json")
        authorization["scope"] = "BATCH"
        duplicate = copy.deepcopy(authorization["bindings"][0])
        duplicate["payload_digest"] = "0" * 64
        authorization["bindings"].append(duplicate)
        with self.assertRaisesRegex(ValidationError, "duplicates an application target"):
            validate_authorization(
                authorization,
                validated,
                parse_datetime("2099-01-01T00:05:00Z", "test time"),
            )

    def test_unknown_answer_cannot_claim_a_value(self) -> None:
        answers = load_json(ASSETS / "answers.json")
        answers["answers"][1]["answer"] = "yes"
        with self.assertRaisesRegex(ValidationError, "while UNKNOWN"):
            validate_answers(answers)

    def test_proceed_decision_rejects_mandatory_unknown(self) -> None:
        profile = load_json(ASSETS / "profile.json")
        job = load_json(ASSETS / "job.json")
        match = load_json(ASSETS / "match.json")
        match["requirements"][0]["state"] = "UNKNOWN"
        match["requirements"][0]["evidence_ids"] = []
        with self.assertRaisesRegex(ValidationError, "cannot be PROCEED"):
            validate_match(match, job, profile)

    def test_match_state_is_code_enforced_when_schema_is_bypassed(self) -> None:
        profile = load_json(ASSETS / "profile.json")
        job = load_json(ASSETS / "job.json")
        match = load_json(ASSETS / "match.json")
        match["requirements"][0]["state"] = "WAIVED"
        with mock.patch("validate_match.validate_against_schema"):
            with self.assertRaisesRegex(ValidationError, "must be one of"):
                validate_match(match, job, profile)

    def test_checkpoint_hash_chain_is_valid(self) -> None:
        validate_checkpoint(load_events(ASSETS / "checkpoint.jsonl"))

    def test_checkpoint_tampering_is_rejected(self) -> None:
        events = load_events(ASSETS / "checkpoint.jsonl")
        events[0]["actor"] = "tampered"
        with self.assertRaisesRegex(ValidationError, "event_hash"):
            validate_checkpoint(events)

    def test_checkpoint_duplicate_json_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.jsonl"
            path.write_text('{"event_id":"first","event_id":"second"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "duplicate key"):
                load_events(path)

    def test_checkpoint_read_error_hides_parent_path(self) -> None:
        path = Path("private-parent") / "checkpoint.jsonl"
        with mock.patch.object(Path, "read_text", side_effect=PermissionError(13, "Permission denied", str(path))):
            with self.assertRaises(ValidationError) as raised:
                load_events(path)
        self.assertIn("checkpoint.jsonl", str(raised.exception))
        self.assertNotIn("private-parent", str(raised.exception))

    def test_action_status_requires_attempt_and_evidence(self) -> None:
        events = load_events(ASSETS / "checkpoint.jsonl")
        events[1]["workflow_status"] = "SUBMITTED"
        events[1]["event_type"] = "APPLICATION_SUBMITTED"
        events[1]["attempt_id"] = None
        events[1]["evidence_refs"] = []
        events[1]["event_hash"] = canonical_digest(events[1], omit={"event_hash"})
        with self.assertRaisesRegex(ValidationError, "attempt_id"):
            validate_checkpoint(events)

    def test_checkpoint_times_cannot_move_backward(self) -> None:
        events = load_events(ASSETS / "checkpoint.jsonl")
        events[1]["occurred_at"] = "2026-01-02T09:00:00Z"
        events[1]["event_hash"] = canonical_digest(events[1], omit={"event_hash"})
        with self.assertRaisesRegex(ValidationError, "earlier than"):
            validate_checkpoint(events)

    def test_checkpoint_equal_timestamps_use_sequence_order(self) -> None:
        events = load_events(ASSETS / "checkpoint.jsonl")
        events[1]["occurred_at"] = events[0]["occurred_at"]
        events[1]["event_hash"] = canonical_digest(events[1], omit={"event_hash"})
        validate_checkpoint(events)

    def test_all_schema_documents_are_json(self) -> None:
        schemas = SKILL_ROOT / "references"
        for path in schemas.glob("*.schema.json"):
            with self.subTest(path=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
