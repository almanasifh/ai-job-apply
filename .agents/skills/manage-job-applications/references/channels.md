# Channel Rules

## General

Before an external action, verify the active account reference, destination, vacancy identity, package digest, artifact hashes, and live approval. Use only supported, user-authorized interfaces.

## Email

Bind approval to the sender account reference, recipients, subject, message body, and attachments. Provider acceptance may establish `SENT`; it does not establish delivery or an employer application outcome.

## Portals

Bind approval to the portal account reference, vacancy, answers, and uploaded artifacts. A first-party confirmation can establish `SUBMITTED`. A timeout or navigation change without confirmation is `SUBMISSION_UNCERTAIN`.

## LinkedIn and similar services

Respect the provider's supported access methods and security controls. Stop at login, CAPTCHA, identity, rate-limit, or anti-automation barriers. Do not evade them.

## Manual handoff

When no authorized connector is available, produce the final package and a checklist for the user. Record it as `READY`, not `SENT` or `SUBMITTED`.
