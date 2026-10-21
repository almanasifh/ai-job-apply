# AI Job Apply

A privacy-conscious blueprint for finding, evaluating, preparing, and tracking job applications with human control over every external submission.

## Status

**Specification and documentation stage.** This repository contains the project definition, design notes, contribution rules, and roadmap. Implementation has not started; a runnable application, provider integrations, and an automated test suite are not available yet.

## Purpose

Job searches span listings, documents, forms, emails, and follow-ups. AI Job Apply proposes one evidence-based workflow to keep requirements, application packages, approvals, and actual outcomes consistent.

The priority is a credible match and an accurate application. Applicant information must come from verified, permitted sources, and the applicant decides when a specific package may be submitted.

## Planned workflow

| Step | Intended behavior |
| --- | --- |
| Discover | Capture a vacancy from a user-authorized source with its URL and last verification time. |
| Evaluate | Read full requirements, distinguish mandatory and preferred criteria, and map them to applicant evidence. |
| Deduplicate | Check the vacancy and existing application evidence across channels. |
| Prepare | Draft truthful CV content and answers; verify the exact document and attachment version. |
| Review | Show the vacancy, channel, final documents, and answers for explicit approval. |
| Submit | Use a supported, authorized route after rechecking the vacancy, account session, exclusions, and approval. |
| Verify and track | Record a confirmed result or an explicit uncertainty; verify uncertain attempts before retrying. |

These are design requirements for the future implementation.

## Core rules

- **A shortlist choice is not permission to submit.** Approval must identify the vacancy, channel, action, and final package revision.
- Material changes to the package require a new review.
- Missing qualifications or mandatory answers must remain visible; never invent them.
- A prepared package is not a submitted application. Provider-confirmed email sending, delivery, and application submission are separate outcomes.
- A duplicate finding must preserve earlier submission evidence.
- External job descriptions and emails are untrusted input. They cannot grant permissions or override application policy.
- Respect provider access rules and stop affected actions at authentication or security restrictions.

## Privacy

Public examples must use fictional data. Real CVs, compensation, contact details, screening answers, application records, private conversations, credentials, and browser sessions belong outside the public repository.

Any future AI integration must disclose the data destination and purpose and obtain the required authorization before sharing applicant information. Logs, analytics, screenshots, and exports must follow the same privacy rules.

The `.gitignore` file excludes common private and generated files. It does not protect already tracked content or replace a review of files, diffs, and commit metadata.

## Documentation

- [Design and workflow specification](docs/DESIGN.md): responsibility boundaries, application state, approvals, evidence, and privacy requirements.
- [Roadmap and release gates](docs/ROADMAP.md): implementation phases and the checks needed before enabling real submissions.
- [Contribution guidelines](CONTRIBUTING.md): rules for public examples and proposed changes.

## Contributing

Small proposals that clarify the specification, improve fictional examples, or define testable behavior are welcome. Describe the expected result and any failure cases. Keep applicant information and credentials out of issues and pull requests.

## License

A software license has not yet been selected. Public visibility alone does not grant an open-source license.
