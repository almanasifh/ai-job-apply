# Version 0.2.1 Release Validation

Validation date: 2026-10-24

Validated packages: portable Markdown and Agent Plugin bundle, plus the Codex compatibility plugin, generated from the 0.2.1 canonical skill

Data boundary: fictional packaged fixtures only

## Release scope

Version 0.2.1 is a packaging and compatibility patch. It does not change the workflow policy or expected behavioral outcomes validated for version 0.2.0.

The patch:

- adds the generated `manage-job-applications.md` standalone skill to the portable ZIP;
- uses a plain unquoted YAML description for broader host compatibility;
- moves schema references to the skill's single-level `references` directory;
- validates every staged archive path and byte against its source tree; and
- synchronizes installation, status, roadmap, and runbook documentation.

## Behavioral evidence

The complete 10-scenario portable-host and isolated Codex-host evaluation from version 0.2.0 remains applicable because version 0.2.1 changes packaging and compatibility only. See [Version 0.2.0 Evaluation Evidence](EVALUATION_RESULTS_V0.2.0.md).

## Deterministic validation

The release candidate passed:

- fixture profile, application, authorization, and checkpoint validation;
- release and evaluation-catalog validation;
- all 23 unit tests;
- the Codex skill validator for the canonical, staged portable, and staged Codex copies; and
- the Codex plugin validator.

The portable archive was inspected and contains both `manage-job-applications.md` and the complete Agent Plugin. The Codex archive contains the complete Codex compatibility plugin.

## Privacy review

The release archives contain no personal email addresses, credentials, private applicant records, or leaked local paths. All packaged applicant fixtures are fictional.

The repository README intentionally identifies the creator, Hussain Almanasif, with the public contact email and LinkedIn profile supplied for attribution. Those contact details are not included in the release archives.

## Candidate checksums

- `job-application-manager-portable.zip`: `8df8257590fa4f19ca509cf2b68b539839de237942b6009c51d600e3307d9296`
- `job-application-manager-codex.zip`: `6fe064e449a1db09ef0dd2f71d0360977fb39cf6959e3746292ae5148c426640`

## Release decision

All version 0.2.1 release gates passed. The candidate is eligible for tagging and publication.
