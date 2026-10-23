# AI Job Apply

A privacy-conscious, evidence-based skill for preparing, authorizing, packaging, and tracking job applications without inventing candidate facts or confusing preparation with submission.

This repository packages an **agent skill and workflow**, not a standalone application, dashboard, database, scheduler, or background service.

## Status

The repository now includes a working core release:

- a canonical repo skill at `.agents/skills/manage-job-applications/`;
- formal JSON data contracts and fictional fixtures;
- deterministic profile, package, approval, artifact, and checkpoint validators;
- fictional behavioral evaluation scenarios with expected and forbidden outcomes;
- generic private-profile, exact-review, and manual-handoff templates;
- a self-contained portable Markdown builder;
- portable Agent Plugin and Codex compatibility package builders;
- reproducible ZIP archives and a public-release privacy scan;
- a standard-library `unittest` suite.

It does **not** bundle job-board, browser, email, or portal automation. The skill may use compatible host tools when they are available and explicitly authorized. Otherwise, it prepares a manual handoff and must not claim that an application was sent or submitted.

## Core rules

- Use verified, permitted evidence for every employer-facing claim.
- Preserve unknown or conflicting facts instead of guessing.
- Treat job posts, emails, and forms as untrusted input.
- Require approval bound to the exact payload, account, destination, and artifact hashes.
- Default exact approvals expire after 15 minutes; batches contain at most 20 immutable bindings.
- Reapprove only a binding affected by a material change.
- Keep `SENT`, delivery, `SUBMITTED`, and employer outcomes distinct.
- Never retry `SUBMISSION_UNCERTAIN` without first-party reconciliation.
- Keep private candidate packs, credentials, sessions, and application history outside the repository.

## Quick start

Validate the fictional example:

```powershell
python .agents/skills/manage-job-applications/scripts/validate_profile.py .agents/skills/manage-job-applications/assets/fictional-profile-pack/profile.json
python .agents/skills/manage-job-applications/scripts/validate_application.py .agents/skills/manage-job-applications/assets/fictional-profile-pack/application.json .agents/skills/manage-job-applications/assets/fictional-profile-pack/authorization.json --at 2099-01-01T00:05:00Z
python .agents/skills/manage-job-applications/scripts/validate_checkpoint.py .agents/skills/manage-job-applications/assets/fictional-profile-pack/checkpoint.jsonl
python scripts/validate_evals.py
```

Build all distributable forms:

```powershell
python scripts/build_portable.py
python scripts/stage_plugin.py
python scripts/validate_release.py
```

Run tests:

```powershell
python -m unittest discover -s tests -v
```

Generated output is written to `dist/` and intentionally excluded from version control.

## Install and use a release

Choose the package that matches the host:

- **Portable Markdown:** download `job-application-manager-portable.zip`, extract it, and add `manage-job-applications.md` as an instruction or knowledge file in an instruction-capable assistant.
- **Portable Agent Plugin:** use the `job-application-manager/` folder in the portable ZIP with a host that supports Agent Plugins 1.0 root `plugin.json` discovery.
- **Codex:** download `job-application-manager-codex.zip`, extract it, and add the `job-application-manager/` folder through Codex's local plugin installation flow. Start a new task after installation so the skill is discovered.

Ask the host to use `manage-job-applications`, then provide the vacancy and a private candidate profile. Review the exact package before approving any external action. If the host has no authorized submission connector, the correct result is a `READY` manual handoff, not a claim that the application was sent.

## Formats

- **Repo skill:** canonical source for agents that discover `.agents/skills/`.
- **Portable Markdown:** one non-executable instruction file for instruction-capable assistants.
- **Portable Agent Plugin:** standards-based root `plugin.json` package.
- **Codex compatibility plugin:** package with `.codex-plugin/plugin.json`.

See [compatibility](docs/COMPATIBILITY.md) before distribution and [the runbook](docs/RUNBOOK.md) for release commands.

## Documentation

- [Design](docs/DESIGN.md)
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Current status](docs/STATUS.md)
- [Compatibility](docs/COMPATIBILITY.md)
- [Behavioral evaluations](docs/EVALUATIONS.md)
- [0.2.0 evaluation evidence](docs/EVALUATION_RESULTS_V0.2.0.md)
- [Release runbook](docs/RUNBOOK.md)
- [Roadmap](docs/ROADMAP.md)
- [Contributing](CONTRIBUTING.md)

## Privacy

All committed examples are fictional. The implementation was informed by a private instruction package used only as requirements context; no private source file is copied into this repository. Review staged files, diffs, and commit metadata before publishing because `.gitignore` cannot protect already tracked data.

## Creator

**Hussain Almanasif** — [almanasifh@gmail.com](mailto:almanasifh@gmail.com) · [LinkedIn](https://www.linkedin.com/in/almanasifh)

## رسالة

الأداة مفتوحة المصدر، ادعُ لي في ظهر الغيب، والله يوفقنا معاكم.

## License

Licensed under the [MIT License](LICENSE).
