# Version 0.4.0 Development Validation

Validation date: 2026-10-27

Branch: `feature/multi-agent-orchestration`

This record covers the committed PR candidate after claim-ledger approval binding, digest hardening, role fixtures, and documentation sync. It is development evidence for the open pull request and does not by itself publish a GitHub release.

## Automated checks

The following commands passed on the Linux checkout:

```powershell
python -m unittest discover -s tests -v
python scripts/validate_evals.py
python scripts/build_portable.py
python scripts/stage_plugin.py
python scripts/validate_release.py
```

Results:

- 100 unit tests passed.
- All 29 fictional evaluation scenarios passed static catalog validation.
- Portable Markdown and both plugin forms rebuilt successfully.
- Release validation passed staged fixtures, contracts, hashes, archives, privacy checks, role envelopes, and claim-ledger authorization binding.
- Clean ZIP installs of the portable and Codex packages passed the four Phase 7 orchestration gates.

Artifact SHA-256 values for this candidate build:

- Portable Markdown: `484e45da134c7de58f42ed23b75739b0611d27656196726884bcbb942ef4747e`
- Portable ZIP: `7bab075ecdef16d92801a04e492aa40feb0f25ded1ff62ff9eed9ce568d1d0ab`
- Codex ZIP: `8d34a9cdc581b389556aa7d1831a8478bf89acea83b0cc28a6a3a03b4d48d8d3`

## Remaining publish gates

- Obtain Windows and Linux CI results for the final committed revision.
- Follow the release runbook only after protected CI is green.
- Do not tag or publish version 0.4.0 from an uncommitted or CI-failing tree.
