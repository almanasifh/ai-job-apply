# Behavioral Evaluations

`evals/behavioral-scenarios.json` contains twenty-nine fictional scenarios. Twenty-seven exercise packaged skill runtime behavior. Two are classified separately through `evidence_scope`:

- `host_capability` — `eval_native-subagent-spawn` records whether a host can spawn real subagent threads. It is not packaged job-skill runtime evidence.
- `release_packaging` — `eval_sensitive-fixture-release-scan` records release-scan privacy controls. It is not packaged job-skill runtime evidence.

The catalog covers source verification, mandatory gaps, truthful claims, unavailable tools, stale, expired, and future approvals, uncertain results, prompt injection, duplicates, batch limits, language alignment, employer exclusions, shortlist authority, required answers, security challenges, outcome separation, artifact QA, delegation privacy and authority, sequential fallback, parallel deduplication, output conflicts, bounded capacity, late specialist results, delegated claims, delegated outcome reconciliation, host spawn capability, and release privacy.

## Validate the catalog

```powershell
python scripts/validate_evals.py
```

The validator checks catalog structure, canonical workflow statuses, risk coverage, unique scenario identifiers, and referenced public files. It does not call an AI model or prove behavioral compliance.

Changes to policy, statuses, approval rules, or behavioral scenarios require new isolated host runs before release evidence may claim that the changed candidate passed.

## Run a scenario

1. Start a clean session in the host being evaluated.
2. Load the packaged `manage-job-applications` skill.
3. Make only the scenario's `available_capabilities` available.
4. Provide the scenario prompt and listed fixtures.
5. Compare the result with every expected and forbidden behavior.
6. Record the host, model, package version, date, result, and material observations.

Do not add private candidate data to evaluation evidence. A host passes a scenario only when all expected behaviors are present and no forbidden behavior occurs.
