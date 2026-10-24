# Skill Implementation Plan

This plan covers a portable agent skill, not an application runtime.

## Goal

Provide a generic job-application workflow that supports explicit candidate profiles, grounds employer-facing content in verified evidence, binds approval to immutable packages, and reports outcomes without overstating what happened.

## Completed core

### Phase 0 — Skill policy

- Define the canonical skill and progressively disclosed references.
- Separate discovery, preparation, approval, external action, and outcome evidence.
- Keep private source packages and applicant data outside the public repository.

### Phase 1 — Contracts and fixtures

- Define profile, answer, job, match, artifact, application, authorization, and event schemas.
- Preserve the canonical workflow status vocabulary.
- Include only a fictional profile, vacancy, package, approval, and checkpoint chain.

### Phase 2 — Deterministic helpers

- Enforce every JSON contract and validate profiles, answer libraries, vacancies, matches, final artifacts, package digests, authorization timing and bindings, action evidence, and checkpoint hash chains.
- Use UTF-8 RFC 8785 canonical JSON for the integer-only contract subset and lowercase SHA-256 digests.
- Reject absolute or escaping artifact paths and unsupported numeric values.

### Phase 3 — Skill distribution

- Generate a self-contained portable Markdown skill.
- Stage the Agent Plugins 1.0 package and Codex compatibility package.
- Normalize archive ordering and timestamps for reproducible ZIP files.
- Scan staged packages for secret patterns, private paths, symlinks, and blocked file types.

## Skill-only boundary

The repository does not implement a dashboard, database, queue, scheduler, background process, provider client, or multi-user service. The skill may coordinate host-provided tools only when those tools are available, supported, and explicitly authorized.

Missing host capabilities result in analysis, preparation, validation, or a manual handoff. They do not justify creating an application runtime or claiming an external action occurred.

## Next skill phases

### Phase 4 — Behavioral evaluations

The fictional scenario catalog and deterministic catalog validator are implemented. Version 0.2.0 recorded portable-host and isolated Codex-host evidence for the original ten scenarios. Version 0.3.0 expands the catalog to eighteen scenarios, including exclusions, shortlist authority, approval timing, required answers, security challenges, outcome separation, and artifact QA. All eight added scenarios passed isolated canonical-skill and standalone portable evaluation.

### Phase 5 — Onboarding and handoff assets

Generic templates are implemented for a private candidate profile, scoped answers, exact-package review, and manual application handoff. The onboarding reference directs agents to copy them into private working locations rather than editing public fixtures.

### Phase 6 — Compatibility hardening

Version 0.2.1 validated canonical, portable, Agent Plugin, and Codex package structure. Version 0.3.0 repairs standalone Markdown navigation, labels executable guidance accurately, rejects non-conforming portable manifests, and runs release checks on Windows and Linux CI.

## Release gates

- Skill and plugin validators pass.
- Unit tests pass without network access or third-party runtime packages.
- Two builds produce byte-identical portable Markdown and ZIP archives.
- Staged packages contain no private records, credentials, absolute user paths, or unsupported file types.
- No instruction, document, or fixture claims that a real external action occurred.
- Documentation consistently identifies the deliverable as an agent skill.

## Evidence boundary

One private instruction package was reviewed as requirements context. No CV, live account, provider session, or complete application history was audited. Those materials are not implementation evidence and must not be added to this repository.
