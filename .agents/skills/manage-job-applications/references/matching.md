# Requirement Matching

Map each requirement independently. Use these states:

- `SUPPORTED`: one or more verified facts directly support the requirement.
- `PARTIAL`: verified evidence supports only part of the requirement.
- `GAP`: verified facts show the requirement is not met.
- `UNKNOWN`: available evidence cannot answer it.
- `NOT_APPLICABLE`: the requirement does not apply, with a reason.

Label each requirement `MANDATORY` or `PREFERRED`. Mandatory gaps and mandatory unknowns remain visible and may block preparation or submission. A numeric or AI-generated score is advisory and cannot override them.

Record one decision after every requirement is mapped:

- `PROCEED`: every mandatory requirement is `SUPPORTED` or `NOT_APPLICABLE`. A mandatory `PARTIAL`, `GAP`, or `UNKNOWN` cannot proceed.
- `REVIEW`: a person should decide because of a mandatory `PARTIAL`, a preferred gap, or another non-blocking uncertainty.
- `BLOCKED`: an employer exclusion or a mandatory `GAP` stops preparation.
- `SKIP`: the user or an explicit policy chooses not to pursue the vacancy.

Record the exact evidence identifiers used. Do not convert adjacent experience, enthusiasm, or a similar title into a claim of direct qualification.
