# Skill Roadmap and Release Gates

This roadmap covers the reusable agent skill only. A standalone application, dashboard, database, scheduler, background worker, and bundled provider client are outside scope.

## Delivery phases

| Phase | Skill deliverable | Exit condition | Status |
| --- | --- | --- | --- |
| 0. Policy core | Scope, workflow, privacy rules, approval model, and status vocabulary | Instructions are consistent and preserve user authorization | Implemented |
| 1. Contracts and fixtures | Profile, job, match, artifact, package, authorization, and event contracts | Fictional examples validate and contain no private applicant data | Implemented |
| 2. Deterministic helpers | Schema-enforced profile, answer, vacancy, match, package, artifact, approval, and checkpoint validation | Invalid contracts, unsafe approvals, failed QA, unsupported outcomes, tampering, stale bindings, and invalid hash chains are detected | Implemented |
| 3. Portable distribution | Repo skill, portable Markdown, Agent Plugin, and Codex compatibility package | Reproducible builds and public-release scans pass | Implemented |
| 4. Behavioral evaluations | Eighteen realistic fictional prompts for discovery, matching, approval, handoff, and uncertainty | Original ten and all eight added scenarios have cross-format host evidence | Implemented and validated |
| 5. Onboarding resources | Generic private-profile setup and manual handoff templates | Private-profile, exact-review, and handoff templates are packaged | Implemented |
| 6. Compatibility hardening | Host capability matrix and repeated release validation | Documented hosts load the skill without implying unavailable tools | Implemented |
| 7. Bounded multi-agent orchestration | Five specialist roles, delegation/result contracts, claim ledger, privacy minimization, and sequential fallback | Contracts reject unauthorized declared inputs and outputs; host permissions enforce actual tool access; approval remains main-only | Implemented; behavioral validation pending |

## Skill behavior gates

A skill release must demonstrate with fictional data that:

- [x] An incomplete source remains unverified.
- [x] Mandatory gaps and unknowns stay visible regardless of score.
- [x] Unsupported profile or CV claims are rejected.
- [x] Exact vacancy duplicates preserve prior evidence.
- [x] Excluded employers are not advanced through preparation.
- [x] A shortlist decision cannot authorize an external action.
- [x] Material package edits invalidate the affected approval binding.
- [x] Exact approvals expire after the configured interval.
- [x] Future-issued approvals remain inactive until `issued_at`.
- [x] Batch approval contains no more than 20 unique immutable application targets.
- [x] Unknown required answers produce an actionable hold.
- [x] Artifacts marked `PENDING` or `FAILED` cannot enter an immutable approved package.
- [x] Missing host tools produce a manual handoff, not a false action claim.
- [x] Authentication, CAPTCHA, and provider restrictions stop the affected action.
- [x] Ambiguous results remain `SUBMISSION_UNCERTAIN` and are not blindly retried.
- [x] `SENT`, delivery, `SUBMITTED`, and employer outcomes remain distinct.
- [x] Untrusted vacancy or email content cannot override skill policy.
- [x] Public packages contain no applicant records, credentials, or local absolute paths.
- [ ] Delegation envelopes bind role, capability, inputs, permitted facts, expiry, and digest in isolated host behavior.
- [ ] Specialist results cannot authorize external action or write canonical outcomes in isolated host behavior.
- [ ] Employer-facing claim ledgers resolve artifact facts to verified permitted evidence in isolated host behavior.
- [ ] Late specialist changes invalidate only the affected approval binding in isolated host behavior.

## Release evidence

Record the tested revision, host, build and validation commands, results, and material limitations. A successful private assisted task does not establish a portable feature unless the reusable skill behavior and public evidence are present. Do not carry forward prior host evidence across material policy or behavioral changes without rerunning the affected scenarios.
