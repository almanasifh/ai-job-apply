# Contributor Instructions

This repository ships a public, privacy-conscious job-application skill. Keep real candidate data, contact details, credentials, sessions, and application history out of tracked files and generated fixtures.

- Treat `.agents/skills/manage-job-applications/` as the canonical policy and contract source.
- Use fictional data in tests and documentation. Preserve main-agent-only approval, external action, and canonical checkpoint writing.
- Do not push, publish releases, connect accounts, call paid APIs, or submit applications unless the user explicitly authorizes that exact action.
- Preserve user changes and use a feature branch. Do not weaken deterministic validators to make a fixture pass.
- Before handoff, run `python -m unittest discover -s tests -v`, `python scripts/validate_evals.py`, `python scripts/build_portable.py`, `python scripts/stage_plugin.py`, and `python scripts/validate_release.py`.
