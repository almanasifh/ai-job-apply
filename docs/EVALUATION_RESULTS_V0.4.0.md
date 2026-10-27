# Version 0.4.0 Evaluation Evidence

Evaluation date: 2026-10-27

Evaluated candidate: `feature/multi-agent-orchestration` after claim-ledger approval binding and digest hardening

Hosts:

- Clean extracted `job-application-manager-portable.zip` Agent Plugin skill tree
- Clean extracted `job-application-manager-codex.zip` skill tree
- Staged portable and Codex plugin skill trees under `dist/`

Evidence method: deterministic packaged validators and fictional fixtures only. No live applicant data, credentials, sessions, or provider actions. This record proves the Phase 7 contract gates on clean installed packages. It does not claim a conversational LLM host replay of every catalog prompt.

## Phase 7 orchestration gates

| Gate | Portable ZIP install | Codex ZIP install | Observation |
| --- | --- | --- | --- |
| Delegation envelopes bind role, capability, inputs, permitted facts, expiry, and digest | Pass | Pass | Matcher fixture validates; expired and future leases reject; input digests match job and minimized-facts bytes. |
| Specialist results cannot authorize external action or write canonical outcomes | Pass | Pass | `external_action_taken: true` is rejected; Tracker outputs remain proposal references. |
| Employer-facing claim ledgers resolve artifact facts to verified permitted evidence | Pass | Pass | Valid ledger binds into authorization; invented evidence identifiers are rejected. |
| Late specialist changes invalidate only the affected approval binding | Pass | Pass | Changed claim-ledger digest fails the existing authorization binding. |

All four gates also passed against the staged portable and Codex plugin trees.

## Catalog classification

The twenty-nine scenario catalog remains the behavioral prompt set. Two scenarios are classified outside packaged skill runtime:

- `eval_native-subagent-spawn` — `evidence_scope: host_capability`
- `eval_sensitive-fixture-release-scan` — `evidence_scope: release_packaging`

The remaining twenty-seven scenarios, including the nine skill-runtime orchestration scenarios, keep their expected and forbidden behaviors unchanged. Prior 0.2.0 and 0.3.0 host evidence remains the cross-host record for the earlier eighteen scenarios.

## Deterministic validation

The candidate passed:

- all 100 unit tests;
- evaluation-catalog validation with `evidence_scope`;
- release validation of staged fixtures, role envelopes, claim ledger, and hash chains;
- two package builds whose ZIP installs independently satisfied the four Phase 7 gates.

## Release decision

Contract and clean-package gate evidence for Phase 7 is complete. Publication of version 0.4.0 remains gated on protected Windows and Linux CI for the final committed revision and the ordinary release runbook.
