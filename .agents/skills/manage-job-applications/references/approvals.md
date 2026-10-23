# Approval Contracts

Approval is explicit, time-bounded, and bound to immutable application content.

## Exact approval

An exact approval contains one binding and normally expires 15 minutes after issue. The binding includes the application identifier and version, candidate, job, channel, account reference, destination, canonical payload digest, and ordered artifact hashes.

## Batch approval

A batch contains 1 to 20 complete immutable bindings. Approval of a search, filter, shortlist, employer, or template is not a batch approval.

Changing one package invalidates only its affected binding; unchanged bindings remain usable until expiry or explicit revocation. Adding a new application requires a new binding.

## Preflight

Immediately before action, verify:

- approval is active and unexpired;
- binding fields exactly match the current package;
- canonical digest and every artifact hash match;
- account/session, destination, and job remain valid;
- there is no prior successful or uncertain attempt requiring reconciliation.

Canonical payload bytes use the RFC 8785 JSON Canonicalization Scheme and UTF-8. Digests are lowercase SHA-256.
