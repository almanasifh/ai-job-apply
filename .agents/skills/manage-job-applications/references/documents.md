# Documents and Answers

Generate employer-facing text from verified, permitted facts only. Keep claims specific enough to audit and conservative enough to remain true.

## Artifact checks

For every CV, cover letter, portfolio, message, or answer set:

1. Record the application and candidate identifiers.
2. Record a repository- or workspace-relative path, media type, and byte count.
3. Compute a lowercase SHA-256 digest from the final bytes.
4. Verify that the displayed filename is the selected file.
5. Record the fact identifiers supporting material claims.
6. Mark the artifact immutable once included in an approval binding.

Any byte change creates a new digest and package revision. Never substitute a similarly named file after approval.

Unknown required answers create `NEEDS_INPUT`; facts requiring documentary confirmation create `NEEDS_VERIFICATION`.
