# Skill Roadmap and Release Gates

This roadmap covers the reusable agent skill only. A standalone application, dashboard, database, scheduler, background worker, and bundled provider client are outside scope.

## Delivery phases

| Phase | Skill deliverable | Exit condition | Status |
| --- | --- | --- | --- |
| 0. Policy core | Scope, workflow, privacy rules, approval model, and status vocabulary | Instructions are consistent and preserve user authorization | Implemented |
| 1. Contracts and fixtures | Profile, job, match, artifact, package, authorization, and event contracts | Fictional examples validate and contain no private applicant data | Implemented |
| 2. Deterministic helpers | Profile, package, artifact, approval, and checkpoint validation | Tampering, stale bindings, and invalid hash chains are detected | Implemented |
| 3. Portable distribution | Repo skill, portable Markdown, Agent Plugin, and Codex compatibility package | Reproducible builds and public-release scans pass | Implemented |
| 4. Behavioral evaluations | Realistic fictional prompts for discovery, matching, approval, handoff, and uncertainty | Portable-host and isolated Codex-host runs passed | Implemented |
| 5. Onboarding resources | Generic private-profile setup and manual handoff templates | Private-profile, exact-review, and handoff templates are packaged | Implemented |
| 6. Compatibility hardening | Host capability matrix and repeated release validation | Documented hosts load the skill without implying unavailable tools | In progress |

## Skill behavior gates

A skill release must demonstrate with fictional data that:

- [ ] An incomplete source remains unverified.
- [ ] Mandatory gaps and unknowns stay visible regardless of score.
- [ ] Unsupported profile or CV claims are rejected.
- [ ] Exact vacancy duplicates preserve prior evidence.
- [ ] Excluded employers are not advanced through preparation.
- [ ] A shortlist decision cannot authorize an external action.
- [ ] Material package edits invalidate the affected approval binding.
- [ ] Exact approvals expire after the configured interval.
- [ ] Batch approval contains no more than 20 immutable bindings.
- [ ] Unknown required answers produce an actionable hold.
- [ ] Missing host tools produce a manual handoff, not a false action claim.
- [ ] Authentication, CAPTCHA, and provider restrictions stop the affected action.
- [ ] Ambiguous results remain `SUBMISSION_UNCERTAIN` and are not blindly retried.
- [ ] `SENT`, delivery, `SUBMITTED`, and employer outcomes remain distinct.
- [ ] Untrusted vacancy or email content cannot override skill policy.
- [ ] Public packages contain no applicant records, credentials, or local absolute paths.

## Release evidence

Record the tested revision, host, build and validation commands, results, and material limitations. A successful private assisted task does not establish a portable feature unless the reusable skill behavior and public evidence are present.
