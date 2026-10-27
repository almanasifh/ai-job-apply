# Exact Application Review

## Identity

- Candidate ID: `{{candidate_id}}`
- Application ID and version: `{{application_id}}` / `{{version}}`
- Employer and role: `{{employer}}` — `{{role}}`
- Job ID and source: `{{job_id}}` — `{{source_url}}`

## Route

- Channel: `{{channel}}`
- Account reference: `{{sender_account_ref}}`
- Destination: `{{destination}}`
- Vacancy last checked: `{{checked_at}}`

## Final Content

- Message or cover letter: `{{exact_message_or_reference}}`
- Screening answers: `{{exact_answers_or_reference}}`
- Payload digest: `{{payload_digest}}`
- Claim ledger digest: `{{claim_ledger_digest}}`

## Artifacts

| Filename | Media type | Bytes | SHA-256 | QA status |
| --- | --- | ---: | --- | --- |
| `{{artifact_filename}}` | `{{media_type}}` | `{{byte_count}}` | `{{sha256}}` | `{{qa_status}}` |

## Requirement Review

- Mandatory gaps: `{{mandatory_gaps_or_none}}`
- Mandatory unknowns: `{{mandatory_unknowns_or_none}}`
- Other unresolved items: `{{unresolved_items_or_none}}`
- Duplicate check: `{{duplicate_result}}`
- Exclusion check: `{{exclusion_result}}`

## Approval Request

Approve only the exact immutable package shown here. Default exact approval expiry: 15 minutes.

- Decision: `APPROVE / MODIFY / DECLINE`
- Approver reference: `{{approver_ref}}`
- Issued at: `{{issued_at}}`
- Expires at: `{{expires_at}}`

This review sheet does not prove that an application was sent or submitted.
