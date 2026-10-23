from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "manage-job-applications"
ASSETS = SKILL_ROOT / "assets" / "fictional-profile-pack"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from common import ValidationError, canonical_digest, canonical_json_bytes, load_json, parse_datetime
from validate_application import validate_application, validate_authorization
from validate_checkpoint import load_events, validate_checkpoint
from validate_profile import validate_profile


class CanonicalJsonTests(unittest.TestCase):
    def test_canonical_json_is_utf8_and_key_sorted(self) -> None:
        self.assertEqual(canonical_json_bytes({"b": 1, "a": "é"}), '{"a":"é","b":1}'.encode("utf-8"))

    def test_floats_are_rejected_to_avoid_nonportable_hashes(self) -> None:
        with self.assertRaises(ValidationError):
            canonical_json_bytes({"value": 1.5})


class ContractTests(unittest.TestCase):
    def test_fictional_profile_is_valid(self) -> None:
        validate_profile(load_json(ASSETS / "profile.json"))

    def test_private_profile_template_is_valid(self) -> None:
        template = SKILL_ROOT / "assets" / "templates" / "profile.template.json"
        validate_profile(load_json(template))

    def test_duplicate_profile_fact_is_rejected(self) -> None:
        profile = load_json(ASSETS / "profile.json")
        profile["facts"].append(copy.deepcopy(profile["facts"][0]))
        with self.assertRaises(ValidationError):
            validate_profile(profile)

    def test_application_and_exact_authorization_are_valid(self) -> None:
        validated = validate_application(load_json(ASSETS / "application.json"), ASSETS)
        validate_authorization(
            load_json(ASSETS / "authorization.json"),
            validated,
            parse_datetime("2099-01-01T00:05:00Z", "test time"),
        )

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

    def test_checkpoint_hash_chain_is_valid(self) -> None:
        validate_checkpoint(load_events(ASSETS / "checkpoint.jsonl"))

    def test_checkpoint_tampering_is_rejected(self) -> None:
        events = load_events(ASSETS / "checkpoint.jsonl")
        events[0]["actor"] = "tampered"
        with self.assertRaisesRegex(ValidationError, "event_hash"):
            validate_checkpoint(events)

    def test_all_schema_documents_are_json(self) -> None:
        schemas = SKILL_ROOT / "references" / "schemas"
        for path in schemas.glob("*.schema.json"):
            with self.subTest(path=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
