# Current Status

## Goal

Ship a generic, reusable job-application agent skill with evidence grounding, exact-package approvals, deterministic helpers, and privacy-safe distribution.

## Current state

Version **0.4.0** is the release candidate. Packaging manifests already declare `0.4.0`. Feature work from pull request #9 is on `main`. Claim-ledger and release-hardening from pull request #10 are ready to merge. No `v0.4.0` GitHub tag or release assets have been published yet; the latest published release remains **0.3.2** until tagging completes.

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

## Next steps

1. Merge pull request #10 into `main`.
2. Rebuild packages from the merge tip, confirm digests, tag `v0.4.0`, and upload release assets.
3. Mark version 0.4.0 as published in this file and the README.
4. Monitor feedback and convert failures into narrow fictional regression scenarios.

## Evidence boundary

One private instruction package was reviewed as requirements context. No CV, live account, provider session, or complete application history was audited, copied, or published.
