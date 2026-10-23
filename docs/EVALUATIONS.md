# Behavioral Evaluations

`evals/behavioral-scenarios.json` contains fictional scenarios for reviewing the skill's decisions. The catalog covers source verification, mandatory gaps, truthful claims, unavailable tools, stale approvals, uncertain results, prompt injection, duplicates, batch limits, and language alignment.

## Validate the catalog

```powershell
python scripts/validate_evals.py
```

The validator checks catalog structure, canonical workflow statuses, risk coverage, unique scenario identifiers, and referenced public files. It does not call an AI model or prove behavioral compliance.

## Run a scenario

1. Start a clean session in the host being evaluated.
2. Load the packaged `manage-job-applications` skill.
3. Make only the scenario's `available_capabilities` available.
4. Provide the scenario prompt and listed fixtures.
5. Compare the result with every expected and forbidden behavior.
6. Record the host, model, package version, date, result, and material observations.

Do not add private candidate data to evaluation evidence. A host passes a scenario only when all expected behaviors are present and no forbidden behavior occurs.
