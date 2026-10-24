# Version 0.3.1 Release Validation

Validation date: 2026-10-25

Validated packages: portable Markdown and Agent Plugin bundle, plus the Codex compatibility plugin, generated from the version 0.3.1 canonical skill

License: MIT

## Scope

Version 0.3.1 is a validator and documentation hardening release. It adds code-level match-state enforcement, rejects duplicate application targets within batch authorizations, caches unchanged schemas, aligns artifact QA code with its `PASSED`-only contract, and documents the evidence-reference and equal-timestamp boundaries.

The workflow policy and behavioral expectations are unchanged from version 0.3.0, so the version 0.3.0 cross-format behavioral evidence remains applicable.

## Local validation

The candidate passed:

- Python source compilation;
- all 44 unit tests;
- release, manifest, fixture, hash-chain, and evaluation-catalog validation;
- two consecutive byte-identical ZIP builds;
- the Codex skill validator for the canonical, staged portable, and staged Codex copies;
- standalone Markdown link validation; and
- package privacy scans.

Focused regressions independently verify code-level match-state enforcement, `PASSED`-only artifact QA, unique batch authorization targets, cached schema loading, and equal checkpoint timestamps ordered by sequence and hash-chain position.

## Behavioral validation

No workflow policy, decision outcome, status transition, or host capability changed in version 0.3.1. The eighteen-scenario version 0.3.0 evidence remains the applicable behavioral record. See [Version 0.3.0 Evaluation Evidence](EVALUATION_RESULTS_V0.3.0.md).

## Continuous integration

Protected Windows and Linux pull-request checks must pass before merge. Record the final pull request and workflow run here before publication.

## Privacy

All packaged examples are fictional. The generated archives contain no creator contact details, credentials, private applicant records, or leaked local paths. Creator attribution remains in the repository README and release notes only.

## SHA-256

- `job-application-manager-codex.zip`: `2448dd561f7a1b42752f9a1a4526b442e683adb35937200abc9480a9a084ed4e`
- `job-application-manager-portable.zip`: `351cba5b3ab59c0abdb6bc9f04ba4714892fded056dae38832793a09b581a0a5`

## Review disposition

All actionable findings from the second review are resolved. The suggested removal of the release validator's sibling-import path setup was not applied because the validator intentionally imports adjacent repository scripts when run directly; removing it would break the documented command without improving package isolation.

## Release decision

Local deterministic gates pass. Version 0.3.1 is eligible for merge, tagging, and publication after protected pull-request checks pass and packaged content remains unchanged.
