# Checkpoints and Events

Use append-only JSON Lines. Each line is one event. Sequence numbers are contiguous per checkpoint and event identifiers are unique.

## Workflow statuses

Use only these statuses. Never create compound or descriptive alternatives.

- `RESEARCHED`: the vacancy is captured and recorded, and no application route has been selected yet.
- `ROUTED`: a channel and destination are selected. Package preparation is not complete.
- `PREPARING`: drafting and artifact work before a complete package is validated and reviewed.
- `READY`: a complete validated package is awaiting approval, submission, or manual handoff.
- `NEEDS_INPUT`: a required answer or decision is unknown and must come from the user.
- `NEEDS_VERIFICATION`: a source, fact, or identity still needs confirmation.
- `TECHNICAL_HOLD`: authentication, a CAPTCHA, a provider restriction, or a missing host tool stopped the affected action.
- `SUBMISSION_UNCERTAIN`: the action may have occurred, but confirmation is missing.
- `SENT`: an email provider accepted the send request.
- `SUBMITTED`: first-party evidence confirms an application submission.
- `DELIVERY_FAILED`: the provider reports that a send was not delivered. This is not an employer outcome.
- `SUBMISSION_FAILED`: the attempt definitively did not submit.
- `SKIPPED`: the user or an explicit policy chooses not to pursue the vacancy.

`DUPLICATE` is a review disposition, not a workflow status. Approval state, attempt state, delivery state, and employer outcome are orthogonal fields or events.

The first event is `RESEARCHED` or `SKIPPED`. A later event may move only to a status in this table. A status may repeat only when it lists itself.

| From | Allowed next statuses |
| --- | --- |
| `RESEARCHED` | `ROUTED`, `PREPARING`, `READY`, `NEEDS_INPUT`, `NEEDS_VERIFICATION`, `TECHNICAL_HOLD`, `SKIPPED` |
| `ROUTED` | `PREPARING`, `READY`, `NEEDS_INPUT`, `NEEDS_VERIFICATION`, `TECHNICAL_HOLD`, `SKIPPED` |
| `PREPARING` | `PREPARING`, `READY`, `NEEDS_INPUT`, `NEEDS_VERIFICATION`, `TECHNICAL_HOLD`, `SKIPPED` |
| `READY` | `READY`, `PREPARING`, `NEEDS_INPUT`, `NEEDS_VERIFICATION`, `TECHNICAL_HOLD`, `SENT`, `SUBMITTED`, `SUBMISSION_UNCERTAIN`, `SUBMISSION_FAILED`, `SKIPPED` |
| `NEEDS_INPUT` | `PREPARING`, `READY`, `NEEDS_INPUT`, `NEEDS_VERIFICATION`, `TECHNICAL_HOLD`, `SKIPPED` |
| `NEEDS_VERIFICATION` | `PREPARING`, `READY`, `NEEDS_INPUT`, `NEEDS_VERIFICATION`, `TECHNICAL_HOLD`, `SKIPPED` |
| `TECHNICAL_HOLD` | `TECHNICAL_HOLD`, `PREPARING`, `READY`, `NEEDS_INPUT`, `NEEDS_VERIFICATION`, `SKIPPED` |
| `SENT` | `SUBMITTED`, `DELIVERY_FAILED`, `SUBMISSION_UNCERTAIN`, `TECHNICAL_HOLD` |
| `SUBMITTED` | `DELIVERY_FAILED`, `TECHNICAL_HOLD` |
| `DELIVERY_FAILED` | `TECHNICAL_HOLD`, `NEEDS_VERIFICATION`, `SKIPPED` |
| `SUBMISSION_FAILED` | `PREPARING`, `READY`, `TECHNICAL_HOLD`, `NEEDS_INPUT`, `NEEDS_VERIFICATION`, `SKIPPED` |
| `SUBMISSION_UNCERTAIN` | `SENT`, `SUBMITTED`, `DELIVERY_FAILED`, `SUBMISSION_FAILED`, `TECHNICAL_HOLD`, `NEEDS_VERIFICATION` |
| `SKIPPED` | none |

`SKIPPED` is terminal. An event after `SUBMISSION_UNCERTAIN` must reuse that same attempt identifier and may move only to a reconciled outcome above. Do not open a new attempt from an uncertain result.

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
