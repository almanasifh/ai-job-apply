# Implementation Plan

This plan converts the design into a reusable, privacy-conscious agent skill. It deliberately separates the portable policy core from provider-specific runtime automation.

## Goal

Provide a generic job-application workflow that supports any number of explicit candidate profiles, grounds employer-facing content in verified evidence, binds approval to immutable packages, and records outcomes without overstating what happened.

## Completed core

### Phase 0 — Repository and policy

- Define the canonical skill and progressive reference set.
- Keep private source packages and applicant data outside the public repository.
- License the implementation under Apache-2.0.

### Phase 1 — Contracts and fixtures

- Define profile, answer, job, match, artifact, application, authorization, and event schemas.
- Preserve the canonical workflow status vocabulary.
- Include only a clearly fictional profile, vacancy, package, approval, and checkpoint chain.

### Phase 2 — Deterministic controls

- Validate profiles, final artifacts, package digests, authorization bindings, expiry, and checkpoint hash chains.
- Use UTF-8 RFC 8785 canonical JSON for the integer-only contract subset and lowercase SHA-256 digests.
- Reject absolute or escaping artifact paths and unsupported numeric values.

### Phase 3 — Distribution

- Generate a self-contained portable Markdown skill.
- Stage the Agent Plugins 1.0 package and the Codex compatibility package.
- Normalize archive order and timestamps for reproducible ZIP files.
- Scan staged packages for common secret patterns, private paths, symlinks, and blocked file types.

## Deferred runtime work

### Phase 4 — Authorized adapters

Add provider-specific email, portal, or browser adapters only when supported interfaces, account scopes, authentication handling, rate limits, and first-party receipts can be tested in an approved environment.

### Phase 5 — Recovery and monitoring

Add reconciliation, controlled retries, scheduled discovery, freshness reporting, and operational alerts. An uncertain attempt must remain non-retryable until reconciled.

### Phase 6 — Product surface

Add a secured dashboard, persistent multi-user storage, access controls, retention/deletion controls, observability, and deployment guidance. UI state must derive from the same durable events as backend actions.

## Release gates

- All skill and plugin validators pass.
- Unit tests pass without network access or third-party Python packages.
- Two builds produce byte-identical portable Markdown and ZIP archives.
- Staged packages contain no private records, credentials, absolute user paths, or unsupported file types.
- No documentation or fixture claims that a real external submission occurred.

## Evidence boundary

One private instruction package was reviewed as requirements context. No CV, live account, provider session, or complete application history was audited. Those materials are not implementation evidence and must not be added to this repository.
