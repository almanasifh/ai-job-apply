# Discovery and Deduplication

Capture a vacancy only from a user-authorized source. Store both `captured_at` and `checked_at`; the latter means the full source was actually reviewed at that time.

## Required capture

- Source URL and source job identifier when available
- Employer, role, location, and channel
- Mandatory and preferred requirements
- Full-content digest and a canonical identity
- Availability or verification state

## Duplicate checks

Compare source identifiers first, then canonical URL, then employer/role/location and content similarity. A duplicate is a review disposition, not a workflow status. Preserve the earlier record and its submission evidence.

Never submit through a second channel merely because the first channel's result is slow or ambiguous. Resolve the existing attempt first.

When first-party evidence already establishes `SUBMITTED`, a newly discovered route is recorded with a duplicate review disposition while the workflow status remains `SUBMITTED`. Do not replace that status with `SKIPPED` or `DUPLICATE`.
