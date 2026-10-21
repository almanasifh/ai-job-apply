# AI Job Apply

A project for organizing job searches, preparing tailored application drafts, and keeping the applicant in control of every submission.

## Current status

**Planning and documentation stage.** This repository contains a project outline and contribution rules. It does not yet contain a runnable application, AI integration, live job search, or automated submission feature.

## Planned workflow

1. Import a job description from a user-provided source.
2. Compare its requirements with facts supplied by the applicant.
3. Flag missing information and possible duplicate applications.
4. Draft a tailored CV and application answers without inventing qualifications.
5. Present the exact job, CV version, and answers for human review.
6. Record a submission only after an authorized action has a verifiable result.

Approval should apply to a specific job and document version. Changes to the CV or answers should require a new review. A prepared application is not a submitted application.

## Planned capabilities

- Job organization and requirement matching.
- CV and answer drafting with clear source facts.
- Application status tracking and duplicate detection.
- Human approval before any external submission.
- Optional AI assistance with explicit control over what data is shared.

## Privacy principles

- Public examples must use fictional data.
- Keep personal profiles, real CVs, compensation, contact details, application records, and conversation exports outside Git.
- Never commit API keys, login cookies, recovery codes, access tokens, or browser sessions.
- Any future AI or service integration must explain what data it sends and obtain user authorization.
- Review filenames, file contents, screenshots, and commit metadata before publishing.

The `.gitignore` file covers common private and generated files. It cannot remove previously committed content or guarantee that every sensitive file is excluded.

## Initial roadmap

- [ ] Define a provider-independent job and application data model.
- [ ] Build a local tracker using fictional sample records.
- [ ] Add requirement matching and evidence-based draft generation.
- [ ] Implement approval tied to the exact application content.
- [ ] Test duplicate detection, approval changes, and submission evidence.
- [ ] Evaluate authorized integrations and publish an installation guide.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Use fictional examples in issues and pull requests. A software license has not yet been selected.
