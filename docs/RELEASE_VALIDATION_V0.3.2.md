# Version 0.3.2 Release Validation

Validation date: 2026-10-25

Validated packages: portable Markdown and Agent Plugin bundle, plus the Codex compatibility plugin, generated from the version 0.3.2 canonical skill

License: MIT

## Scope

Version 0.3.2 is a reliability, privacy, and repository-hygiene release. It makes package tests hermetic, retries transient directory-not-empty staging cleanup failures, converts filesystem failures into sanitized validation errors, scopes private-data ignore rules without hiding reviewed fixtures, documents the supported JSON Schema subset, links release downloads directly, and adds private vulnerability reporting guidance.

The workflow policy and behavioral expectations are unchanged from version 0.3.1, so the version 0.3.0 cross-format behavioral evidence remains applicable.

## Local validation

The candidate passed:

- Python source compilation;
- all 52 unit tests on local Python 3.14;
- release, manifest, fixture, hash-chain, and evaluation-catalog validation;
- two consecutive byte-identical ZIP builds;
- the Codex skill validator for the canonical, staged portable, and staged Codex copies;
- standalone Markdown link validation; and
- package privacy scans.

Focused regressions verify isolated package output, exclusion of untracked files without modifying the canonical skill, transient `ENOTEMPTY` recovery, scoped ignore behavior, sanitized file and checkpoint errors, path traversal rejection, absolute-path redaction, and path-resolution failure handling.

## Compatibility validation

Pull request [#7](https://github.com/almanasifh/ai-job-apply/pull/7) passed both matrix jobs in GitHub Actions run `40211291228`. Each job ran the full release pipeline on Python 3.11 and reran compilation and all 52 tests on Python 3.12, 3.13, and 3.14:

- `Validate on ubuntu-latest`: passed;
- `Validate on windows-latest`: passed.

The implementation commit was `64e9a99`. The release-evidence-only follow-up commit must pass the same protected checks before merge.

## Behavioral validation

No workflow policy, decision outcome, status transition, or host capability changed in version 0.3.2. The eighteen-scenario version 0.3.0 evidence remains the applicable behavioral record. See [Version 0.3.0 Evaluation Evidence](EVALUATION_RESULTS_V0.3.0.md).

## Privacy and security

All packaged examples are fictional. The generated archives contain no creator contact details, credentials, private applicant records, or leaked local paths. Runtime filesystem failures expose only a filename or generic path category rather than a host-specific absolute path. GitHub secret scanning and push protection remain enabled, and private vulnerability reporting is enabled with guidance in `SECURITY.md`.

## SHA-256

- `job-application-manager-codex.zip`: `da2cfdfa6c9a7e33786bfe3a0c5bd7c99bf1f448c110af7b36636cd067ecc43a`
- `job-application-manager-portable.zip`: `a0af4dfa140951a8c67be0585c2b6dfe4cb928950f213bc3bed1869f48b6dd52`

## Release decision

Local deterministic and protected compatibility gates pass. Version 0.3.2 is eligible for merge, tagging, and publication after the release-evidence-only follow-up passes the same checks and packaged content remains unchanged.
