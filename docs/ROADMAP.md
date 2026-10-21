# Roadmap and Release Gates

This roadmap orders the proposed software work. The public deliverable currently consists of documentation and contribution/ignore safeguards.

## Delivery phases

| Phase | Deliverable | Exit condition | Status |
| --- | --- | --- | --- |
| 0. Definition | Scope, workflow, privacy principles, design, and contribution rules. | Documentation is consistent and contains no applicant records. | Documented |
| 1. Local tracker | Manual vacancy import, fictional fixtures, durable records, and an event ledger. | Records survive restart; duplicates preserve prior evidence. | Planned |
| 2. Evidence and documents | Requirement mapping, truthful drafts, artifact revisions, and attachment checks. | Unsupported claims and mismatched attachments are detected. | Planned |
| 3. Review and approval | Search/Apply views, package-specific authorization, approval invalidation, and concurrency protection. | Shortlisting cannot submit, and stale approvals cannot authorize changed packages. | Planned |
| 4. Authorized integrations | Supported discovery and application adapters with explicit permission scopes. | Authorized test actions produce verifiable results and precise failures. | Planned |
| 5. Recovery and scheduled discovery | Receipt reconciliation, controlled retries, monitored polling, and freshness reporting. | Uncertain results cannot trigger blind retries; source-check times are accurate. | Planned |
| 6. Production readiness | Authentication, privacy controls, tests, observability, installation, and deployment guidance. | Security and privacy gates pass in an approved test environment. | Planned |

Choose a software license before presenting a release as licensed open-source software. This roadmap does not select a license.

## Acceptance tests before enabling real submissions

A release must demonstrate, using fictional fixtures or an approved test environment, that:

- [ ] A source with incomplete requirements stays unverified.
- [ ] A disqualifying mandatory gap cannot be overruled by an AI score.
- [ ] Unsupported CV claims and mismatched attachments are blocked.
- [ ] A second channel does not submit the same vacancy twice.
- [ ] Excluded employers are filtered across all supported channels.
- [ ] A shortlist `Yes` without final authorization cannot submit.
- [ ] Material edits after approval invalidate the old approval.
- [ ] Unknown required answers produce a specific actionable hold.
- [ ] Unavailable login, CAPTCHA, or service restrictions stop affected actions safely.
- [ ] An ambiguous submit result stays uncertain until first-party verification.
- [ ] Email `SENT`, message delivery, and application `SUBMITTED` remain distinct.
- [ ] A UI action has an actual secured backend path and correct feedback.
- [ ] Logs and sample exports contain no applicant data or credentials.
- [ ] Search, dashboard, and application records agree after a restart.

### Additional consistency and privacy checks

- [ ] Concurrent requests cannot submit the same applicant/vacancy package twice.
- [ ] Untrusted job descriptions and emails cannot change policy, authorize actions, or extract private data.
- [ ] AI/provider requests contain only permitted data and use the required authorization.
- [ ] Access control, session expiry, encryption, retention, deletion, and export behavior are verified before production use.
- [ ] Scheduled search reports actual check times, operating limits, and failures.

## Evidence required for a release

Record the tested revision, environment, commands or procedures, results, and material limitations. Use authorized test receipts and redact private information before publishing evidence.

Mark a capability implemented only when its source and verification are present. A design document or a successful private assisted task does not establish a reusable software feature.
