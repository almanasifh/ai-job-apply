# Current Status

## Goal

Ship a generic, reusable job-application agent skill with evidence grounding, exact-package approvals, deterministic helpers, and privacy-safe distribution.

## Current state

Version **0.4.0** is the latest published release. Packaging manifests, portable and Codex archives, checksums, and release validation evidence are synchronized at tag `v0.4.0`.

This repository contains no standalone application runtime, dashboard, database, scheduler, background service, or bundled provider client. The skill may use compatible host tools when available and authorized; otherwise it prepares analysis, drafts, checkpoints, or a manual handoff and must not claim an external action occurred.

## Active files

- `.agents/skills/manage-job-applications/` — canonical instructions, references, schemas, scripts, and fictional fixtures.
- `packaging/` — portable Agent Plugin and Codex compatibility manifest sources.
- `scripts/` — deterministic skill builders and release checks.
- `tests/` — contract, semantic safety, privacy, and packaging tests.
- `evals/` — twenty-nine fictional behavioral scenarios with expected and forbidden outcomes.
- `.github/workflows/` — Windows and Linux continuous integration.
- `docs/` — skill scope, design, compatibility, and release guidance.
- `.codex/` — optional source-checkout Codex adapters (not packaged in release ZIPs).

## Changes made

- Added evidence, privacy, approval, channel, and checkpoint policy.
- Added formal contracts, fictional fixtures, and deterministic validators.
- Added portable Markdown and dual plugin packaging with reproducible ZIP archives.
- Expanded the behavioral catalog to twenty-nine scenarios with cross-format evidence for the earlier eighteen.
- Published versions 0.3.0 through 0.3.2 with protected Windows and Linux CI.
- Added bounded Scout, Matcher, Drafter, Verifier, and Tracker orchestration with claim-ledger approval bindings.
- Hardened claim-ledger CLI validation, role digest release checks, Scout/Tracker evidence bans, and review-template alignment.
- Published synchronized version 0.4.0 portable and Codex archives, checksums, evaluation evidence, and release validation evidence.

## Next steps

1. Monitor public feedback and convert demonstrated failures into narrow fictional regression scenarios.
2. Keep manifests, evidence, checksums, installation guidance, and the latest published release synchronized.
3. Continue requiring protected Windows and Linux CI before changes reach `main`.

## Evidence boundary

One private instruction package was reviewed as requirements context. No CV, live account, provider session, or complete application history was audited, copied, or published.
