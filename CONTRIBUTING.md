# Contributing

This project packages a reusable agent skill. Keep proposed changes focused on skill behavior, references, deterministic helpers, fictional fixtures, compatibility, or distribution.

## Before publishing

- Use fictional names, employers, jobs, and application records in examples.
- Do not attach real CVs, contact details, salary information, private messages, or screenshots containing personal data.
- Do not include credentials, API keys, session cookies, recovery codes, or authenticated browser state.
- Check staged files and their diff; `.gitignore` does not protect files already tracked by Git.
- Use a GitHub-provided `noreply` address for public commit metadata if you want to keep your email private.

## Skill behavior

- Separate planned capabilities from working features in documentation.
- Never invent an applicant's employment history, qualifications, answers, or submission results.
- Keep human approval tied to a specific job, CV version, and set of answers.
- Treat changed application content as requiring renewed approval.
- Use only host tools the user has authorized and the service permits.
- Do not add a standalone app, dashboard, database, scheduler, or provider client without a separate explicit scope change.

## Reporting issues

Explain the expected behavior, actual behavior, and steps to reproduce using fictional data. Remove personal information and secrets from logs before sharing them. Never post live credentials in a public issue.
