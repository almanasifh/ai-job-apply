# Version 0.3.0 Release Validation

Validation date: 2026-10-24

Validated packages: portable Markdown and Agent Plugin bundle, plus the Codex compatibility plugin, generated from the version 0.3.0 canonical skill

License: MIT

## Scope

Version 0.3.0 hardens formal contracts, approval timing, artifact QA, checkpoint evidence, standalone navigation, privacy scanning, manifest validation, and cross-platform automation. It expands the behavioral catalog from ten to eighteen fictional scenarios.

## Local validation

The candidate passed:

- Python source compilation;
- all 39 unit tests;
- release, manifest, fixture, hash-chain, and evaluation-catalog validation;
- two consecutive byte-identical ZIP builds;
- the Codex skill validator for the canonical, staged portable, and staged Codex copies;
- standalone Markdown link validation;
- package privacy scans; and
- adversarial regressions for future approvals, failed artifact QA, schema drift, unsupported action evidence, duplicate JSON keys, non-finite JSON numbers, unknown manifest fields, and private-path or email leaks.

## Behavioral validation

The original ten scenarios retain their recorded version 0.2.0 cross-host evidence. All eight added and materially affected scenarios passed in fresh isolated sessions against both the canonical skill and the generated standalone portable Markdown. See [Version 0.3.0 Evaluation Evidence](EVALUATION_RESULTS_V0.3.0.md).

## Continuous integration

Pull request [#1](https://github.com/almanasifh/ai-job-apply/pull/1) passed both matrix jobs in GitHub Actions run `40087724726`:

- `Validate on ubuntu-latest`: passed;
- `Validate on windows-latest`: passed.

The implementation commit was `cb73e33`. Any later commit in the pull request is limited to release evidence and must pass the same protected checks before merge.

## Privacy

All packaged examples are fictional. The generated archives contain no creator contact details, credentials, private applicant records, or leaked local paths. Creator attribution remains in the repository README and release notes only.

## SHA-256

- `job-application-manager-codex.zip`: `50d34a305c411d9a28bc33d2c3f00c7b97137f5567ee2f7086fa7e3758357a97`
- `job-application-manager-portable.zip`: `3d4870ce6322866ab062a2002a4b162350b3aa9ec6fc8e775c2fbf3eb26bdc9b`

## Release decision

Local deterministic, cross-format behavioral, and protected CI gates pass. Version 0.3.0 is eligible for merge, tagging, and publication if later pull-request checks remain green and packaged content does not change.
