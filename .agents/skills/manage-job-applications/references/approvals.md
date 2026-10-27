# Approval Contracts

Approval is explicit, time-bounded, and bound to immutable application content.

## Exact approval

An exact approval contains one binding and normally expires 15 minutes after issue. The binding includes the application identifier and version, candidate, job, channel, account reference, destination, canonical payload digest, ordered artifact hashes, and a validated claim-ledger digest.

## Batch approval

A batch contains 1 to 20 complete immutable bindings. Approval of a search, filter, shortlist, employer, or template is not a batch approval.

Reject an approval request containing more than 20 bindings and perform no action under it. If the individual packages are otherwise complete and immutable, keep their workflow status `READY`; split them into valid batches and obtain separate approval rather than assigning a technical hold.

Changing one package invalidates only its affected binding; unchanged bindings remain usable until expiry or explicit revocation. Adding a new application requires a new binding.

## Multi-agent fan-in

Do not request approval until all required specialist results have returned or been explicitly discarded, their contracts and referenced outputs validate, the claim ledger validates against verified permitted facts, and the main agent has recomputed the final package, artifact, and claim-ledger digests. Bind `claim_ledger_digest` into the approval. A late specialist result is outside the approved package. If it changes bound content, including the claim ledger, obtain a new approval for the affected binding.

Only the main agent may present, hold, or use an approval. Delegating preparation never delegates submission authority.

## Preflight

Immediately before action, verify:

- approval has reached `issued_at` and is still unexpired;
- binding fields exactly match the current package;
- canonical digest, every artifact hash, and the claim-ledger digest match;
- account/session, destination, and job remain valid;
- there is no prior successful or uncertain attempt requiring reconciliation.

Canonical payload bytes use the RFC 8785 JSON Canonicalization Scheme and UTF-8. Digests are lowercase SHA-256.
