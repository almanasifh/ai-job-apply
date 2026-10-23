# Candidate Profiles

Use one canonical profile per candidate. A profile may reference separate answer and preference files, but all employer-facing facts must resolve to evidence.

## Fact model

Each fact has a stable identifier, key, value, status, source, verification time, and allowed uses. Only `VERIFIED` facts may support claims. `UNKNOWN` facts remain unanswered. `CONFLICTING` facts block affected claims until resolved.

Allowed uses limit where a fact may appear, such as `CV`, `COVER_LETTER`, `SCREENING`, or `CONTACT`. Do not infer permission from possession of the data.

## Multiple profiles

Keep candidate identifiers explicit in every job match, package, authorization, and event. Never merge facts between candidates. The skill supports any number of profiles, but an application package binds exactly one candidate.

## Verification

Before use, validate the profile with `scripts/validate_profile.py`. Revalidate if facts, evidence, permissions, or answers change.
