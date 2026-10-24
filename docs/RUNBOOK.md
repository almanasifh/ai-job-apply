# Build and Release Runbook

Run commands from the repository root with Python 3.11 or newer.

## Validate canonical fixtures

```powershell
python .agents/skills/manage-job-applications/scripts/validate_profile.py .agents/skills/manage-job-applications/assets/fictional-profile-pack/profile.json
python .agents/skills/manage-job-applications/scripts/validate_answers.py .agents/skills/manage-job-applications/assets/fictional-profile-pack/answers.json
python .agents/skills/manage-job-applications/scripts/validate_job.py .agents/skills/manage-job-applications/assets/fictional-profile-pack/job.json
python .agents/skills/manage-job-applications/scripts/validate_match.py .agents/skills/manage-job-applications/assets/fictional-profile-pack/match.json .agents/skills/manage-job-applications/assets/fictional-profile-pack/job.json .agents/skills/manage-job-applications/assets/fictional-profile-pack/profile.json
python .agents/skills/manage-job-applications/scripts/validate_application.py .agents/skills/manage-job-applications/assets/fictional-profile-pack/application.json .agents/skills/manage-job-applications/assets/fictional-profile-pack/authorization.json --at 2099-01-01T00:05:00Z
python .agents/skills/manage-job-applications/scripts/validate_checkpoint.py .agents/skills/manage-job-applications/assets/fictional-profile-pack/checkpoint.jsonl
```

## Build outputs

```powershell
python scripts/build_portable.py
python scripts/stage_plugin.py
```

The stage command creates normalized ZIP archives as well as unpacked plugin folders under `dist/`. The portable ZIP contains both the standalone `manage-job-applications.md` file and the Agent Plugin package.

## Validate release

```powershell
python scripts/validate_release.py
python scripts/validate_evals.py
python -m unittest discover -s tests -v
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
python -m pip install PyYAML
$skillValidator = Join-Path $codexHome 'skills\.system\skill-creator\scripts\quick_validate.py'
$pluginValidator = Join-Path $codexHome 'skills\.system\plugin-creator\scripts\validate_plugin.py'
if (Test-Path $skillValidator) { python $skillValidator .agents\skills\manage-job-applications }
if (Test-Path $pluginValidator) { python $pluginValidator dist\codex-plugin\job-application-manager }
```

The final checks use optional local Codex development tooling and its PyYAML dependency when those validators are installed. Their paths may differ on another machine. The skill's own validators, builders, tests, and CI remain standard-library only.

## Publish checklist

- Confirm `git status --short` contains only intended public files.
- Inspect the staged package and archive listings.
- Confirm version parity across all three metadata files.
- Confirm all examples remain fictional.
- Confirm no real profile, CV, answer, receipt, credential, session, or application record is tracked.
- Record the tested revision, commands, results, and known capability limits.
- Re-run every added or materially affected behavioral scenario in isolated target hosts.
