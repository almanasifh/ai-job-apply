from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_evals import EvaluationError, load_catalog, validate_catalog


CATALOG = REPO_ROOT / "evals" / "behavioral-scenarios.json"


class SkillEvaluationCatalogTests(unittest.TestCase):
    def test_catalog_is_valid_and_complete(self) -> None:
        catalog = load_catalog(CATALOG)
        validate_catalog(catalog, repo_root=REPO_ROOT)
        self.assertEqual(len(catalog["scenarios"]), 18)

    def test_unknown_workflow_status_is_rejected(self) -> None:
        catalog = copy.deepcopy(load_catalog(CATALOG))
        catalog["scenarios"][0]["expected_status"] = "DUPLICATE"
        with self.assertRaisesRegex(EvaluationError, "not canonical"):
            validate_catalog(catalog, repo_root=REPO_ROOT)

    def test_missing_fixture_is_rejected(self) -> None:
        catalog = copy.deepcopy(load_catalog(CATALOG))
        catalog["scenarios"][0]["fixture_refs"] = ["private/missing-profile.json"]
        with self.assertRaisesRegex(EvaluationError, "does not exist"):
            validate_catalog(catalog, repo_root=REPO_ROOT)

    def test_missing_risk_coverage_is_rejected(self) -> None:
        catalog = copy.deepcopy(load_catalog(CATALOG))
        catalog["scenarios"] = [
            scenario for scenario in catalog["scenarios"] if "language" not in scenario["risk_tags"]
        ]
        with self.assertRaisesRegex(EvaluationError, "missing risk coverage"):
            validate_catalog(catalog, repo_root=REPO_ROOT)


if __name__ == "__main__":
    unittest.main()
