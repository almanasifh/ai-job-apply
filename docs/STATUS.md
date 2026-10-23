# Current Status

## Goal

Ship a generic, reusable job-application agent skill with evidence grounding, exact-package approvals, deterministic helpers, and privacy-safe distribution.

## Current state

Skill-only version 0.2.0 includes the core workflow, four distribution forms, a fictional behavioral evaluation catalog, and generic onboarding/handoff templates. This repository contains no standalone application runtime, dashboard, database, scheduler, background service, or bundled provider client.

The skill can use compatible host tools when they are available and authorized. Without those tools, it produces analysis, validated drafts, checkpoints, or manual handoffs and does not claim an external action occurred.

## Active files

- `.agents/skills/manage-job-applications/` — canonical instructions, references, schemas, scripts, and fictional fixtures.
- `packaging/` — portable Agent Plugin and Codex compatibility manifest sources.
- `scripts/` — deterministic skill builders and release checks.
- `tests/` — contract and packaging tests.
- `evals/` — fictional behavioral scenarios with expected and forbidden outcomes.
- `docs/` — skill scope, design, compatibility, and release guidance.

## Changes made

- Added evidence, privacy, approval, channel, and checkpoint policy.
- Added formal contracts and fictional end-to-end fixtures.
- Added RFC 8785-subset canonicalization, SHA-256 hashing, and semantic validators.
- Added portable Markdown and dual plugin staging with reproducible ZIP archives.
- Added fictional behavioral evaluations and deterministic catalog validation.
- Added private-profile, answer, exact-review, and manual-handoff templates.
- Added MIT licensing and skill-only documentation.

## Failed attempts

- The environment did not include `jsonschema` or `rfc8785`, so deterministic helpers use a dependency-free RFC 8785-compatible integer-only JSON subset.
- An app-style SQLite tracker was briefly started after an ambiguous continuation request. It was never committed and has been completely removed after scope clarification.
- The first GitHub push was rejected by email-privacy protection; the unpushed commit was amended to use the repository-local GitHub noreply address and then pushed successfully.

## Next steps

1. Execute and record the fictional scenarios across documented compatible hosts.
2. Add any narrow skill corrections demonstrated by those runs.
3. Publish the validated 0.2.0 skill packages.

## Evidence boundary

One private instruction package was reviewed as requirements context. No CV, live account, provider session, or complete application history was audited, copied, or published.
