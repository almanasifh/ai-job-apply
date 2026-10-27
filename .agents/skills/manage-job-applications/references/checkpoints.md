# Checkpoints and Events

Use append-only JSON Lines. Each line is one event. Sequence numbers are contiguous per checkpoint and event identifiers are unique.

## Workflow statuses

`RESEARCHED`, `ROUTED`, `PREPARING`, `READY`, `NEEDS_INPUT`, `NEEDS_VERIFICATION`, `TECHNICAL_HOLD`, `SUBMISSION_UNCERTAIN`, `SENT`, `SUBMITTED`, `DELIVERY_FAILED`, `SUBMISSION_FAILED`, `SKIPPED`.

`DUPLICATE` is a review disposition, not a workflow status. Approval state, attempt state, delivery state, and employer outcome are orthogonal fields or events.

Use only the listed workflow statuses; never create compound or descriptive alternatives. `PREPARING` covers drafting and artifact work before a complete package is validated and reviewed. `READY` requires a complete validated package that is awaiting approval, submission, or manual handoff.

## Hash chain

The first event uses `previous_event_hash: null`. Every later event carries the prior event's `event_hash`. To calculate `event_hash`, omit that field, canonicalize the remaining event with RFC 8785, encode as UTF-8, and calculate lowercase SHA-256.

## Actor discipline

Only the main agent writes the canonical checkpoint. Specialist results are immutable referenced inputs and must not directly assert workflow status. A Tracker may prepare a sanitized checkpoint proposal or recommend an outcome from bounded first-party evidence, but the main agent validates and records it.

## Outcome discipline

- `SENT` means an email provider accepted the send request.
- `SUBMITTED` means first-party evidence confirms an application submission.
- `SUBMISSION_UNCERTAIN` means the action may have occurred but confirmation is missing.
- Never retry an uncertain attempt until reconciled against first-party evidence.

Every action outcome (`SENT`, `SUBMITTED`, `SUBMISSION_UNCERTAIN`, `DELIVERY_FAILED`, or `SUBMISSION_FAILED`) requires an attempt identifier and at least one evidence reference. Evidence references are opaque identifiers: the validator checks presence and uniqueness, while the host must resolve them to trustworthy first-party records before asserting an outcome.

Event times cannot move backward. Equal timestamps are allowed because sequence numbers and the hash chain provide deterministic ordering for events recorded at the same instant.

The hash chain detects changes only when a trusted head hash or prior copy is retained separately. It does not prevent someone who can rewrite the entire checkpoint from recomputing every hash.
