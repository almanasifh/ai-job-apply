# Version 0.4.0 Release Validation

Validation date: 2026-10-27

Validated packages: portable Markdown and Agent Plugin bundle, plus the Codex compatibility plugin, generated from the version 0.4.0 canonical skill

License: MIT

## Scope

Version 0.4.0 adds bounded multi-agent orchestration for hosts that can delegate work. It ships five specialist roles (Scout, Matcher, Drafter, Verifier, Tracker), immutable delegation and specialist-result contracts, an employer-facing claim ledger bound into approvals, sequential fallback when subagents are unavailable, nested role packaging, and deterministic validators for the new contracts.

Approval, external action, and canonical checkpoint writing remain main-agent-only. Custom Codex agent definitions under `.codex/` are optional source-checkout adapters and are not packaged into the release ZIPs. They inherit parent-session permissions and are not a sandbox boundary.

## Local validation

The candidate passed:

- all 107 unit tests;
- evaluation-catalog validation, including `evidence_scope` classification;
- release, manifest, fixture, role-digest, claim-ledger, hash-chain, and privacy validation;
- two consecutive byte-identical ZIP builds from a clean staged skill tree;
- clean ZIP-install proofs of the four Phase 7 orchestration gates on both portable and Codex packages.

Focused regressions cover claim-ledger CLI validation against the profile, required `claim_ledger_digest` bindings, Scout/Tracker candidate-evidence bans, non-null VERIFIED application answers, and role fixture digest cross-checks.

## Compatibility validation

Pull request [#10](https://github.com/almanasifh/ai-job-apply/pull/10) landed on `main` as `e2b148e`. Protected CI run `40581479571` passed both matrix jobs on that merge tip. Each job ran the full release pipeline on Python 3.11 and reran compilation and unit tests on Python 3.12, 3.13, and 3.14:

- `Validate on ubuntu-latest`: passed;
- `Validate on windows-latest`: passed.

Pull request [#9](https://github.com/almanasifh/ai-job-apply/pull/9) previously landed the orchestration feature on `main`.

## Behavioral validation

Phase 7 contract gates were proven on clean installed portable and Codex packages. See [Version 0.4.0 Evaluation Evidence](EVALUATION_RESULTS_V0.4.0.md). The earlier eighteen scenarios keep their version 0.2.0 and 0.3.0 cross-format host evidence. Two catalog scenarios remain classified outside packaged skill runtime (`host_capability` and `release_packaging`).

## Privacy and security

All packaged examples are fictional. The generated archives contain no creator contact details, credentials, private applicant records, or leaked local paths. Public release scanning rejects email-shaped values and absolute user paths even when labeled fictional.

## SHA-256

- Portable Markdown: `eb628a431621cacd7b7da9cf671a01f8b554778f343769d505befe2aa3ff15b7`
- `job-application-manager-portable.zip`: `6b30e379265e2dce87e677de95262441022d15edaf276d4f2d3edbe949d0a78c`
- `job-application-manager-codex.zip`: `c14fb284493bd8a37ec2c952ff901485d512d0bd3185767a764a431024d76221`

## Release decision

Local deterministic gates and protected Windows/Linux CI pass on `main` tip `e2b148e`. Package digests above were rebuilt from that revision. Version 0.4.0 was tagged and published at https://github.com/almanasifh/ai-job-apply/releases/tag/v0.4.0.
