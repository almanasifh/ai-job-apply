# Private Profile Onboarding

Read this reference when the user needs to create or update a candidate profile, answer library, exact-package review, or manual handoff.

## Storage boundary

Create private working copies outside the public skill package. If work must occur inside this repository, use an ignored `private/` directory and verify that no private file is staged before committing.

Never place real candidate data in `assets/fictional-profile-pack/`, public tests, generated plugin archives, or behavioral evaluation evidence.

## Profile setup

1. Copy `assets/templates/profile.template.json` to a private working location.
2. Assign one stable `cand_...` identifier.
3. Replace the starter fact with separately sourced facts.
4. Mark each fact `VERIFIED`, `UNKNOWN`, or `CONFLICTING`.
5. Add a specific source, verification time, and allowed uses for verified facts.
6. Record target roles, locations, channels, and exclusions without publishing them.
7. Run `scripts/validate_profile.py` against the private copy.

Do not turn missing information into a negative answer. Keep unresolved legal, eligibility, compensation, and declaration questions explicit.

## Answer setup

Copy `assets/templates/answers.template.json` to a private location. Scope each answer as `GLOBAL`, `COUNTRY`, `EMPLOYER`, or `JOB`. A verified answer needs evidence identifiers; an unknown answer remains `null` with no evidence.

## Exact review

Use `assets/templates/application-review.template.md` to present the final package. Replace every placeholder, list all unresolved items, and show the exact channel, account reference, destination, payload digest, and artifact hashes before requesting approval.

The review document is not approval by itself. Record approval separately using the authorization contract.

## Manual handoff

Use `assets/templates/manual-handoff.template.md` only when the package is ready but no authorized external-action tool is available. Preserve the exact approved content and clearly label every action the user must perform.

A handoff remains `READY`; it is not `SENT` or `SUBMITTED`.
