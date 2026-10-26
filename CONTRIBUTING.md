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
- Keep subagent tasks bounded by role, input digest, capability set, permitted facts, and expiry.
- Keep approval holding, external action, and canonical checkpoint writing with the main agent.
- Do not add a standalone app, dashboard, database, scheduler, or provider client without a separate explicit scope change.

## Validation

- Add regression tests for contract, policy, packaging, or privacy changes.
- Run `python -m unittest discover -s tests -v`, `python scripts/stage_plugin.py`, `python scripts/validate_release.py`, and `python scripts/validate_evals.py` before opening a pull request.
- Keep the Windows and Linux CI checks passing before merge.
- Submit changes through a pull request because `main` is protected from direct pushes.

### JSON Schema subset

The dependency-free validator intentionally supports only the keywords listed in `SCHEMA_KEYWORDS` in `.agents/skills/manage-job-applications/scripts/common.py`. Unsupported keywords, including `anyOf`, `oneOf`, `allOf`, `not`, `maxLength`, `minProperties`, and `maxProperties`, are rejected when schemas load rather than ignored. Add validator behavior and regression tests before introducing another keyword.

## Reporting issues

Explain the expected behavior, actual behavior, and steps to reproduce using fictional data. Remove personal information and secrets from logs before sharing them. Never post live credentials in a public issue. Report security or privacy vulnerabilities through the process in [SECURITY.md](SECURITY.md).
