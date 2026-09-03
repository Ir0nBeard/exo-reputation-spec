# Security Policy

## Reporting a vulnerability

Please report security issues **privately**. Do not open a public issue for a
vulnerability.

- **Preferred:** GitHub private security advisory at
  https://github.com/Ir0nBeard/exo-reputation-spec/security/advisories
- **Alternative:** email security@exo-trust.com (include the repository name
  in the subject line).

Include, if available: the affected file(s), a minimal reproduction, and the
impact you observed. You should receive an acknowledgement within 3 business
days and a status update within 10 business days.

## Scope

In scope: the reference verifier (`verifier/`), the JSON Schema (`schema/`),
and the specification (`spec/`). The schema `$id` is a canonical identifier
that third parties pin, so a vulnerability in this repository can affect
anything that pins it — that is why private disclosure matters. Anything
deployed in production that *uses* the standard is out of scope for this
repository's policy; contact the operator of that deployment.

## Notes

This repository holds a specification and a reference implementation — no
funds, no keys, no production services. Example envelopes under
`tests/vectors/` are public test data signed with a throwaway example key.
Production issuer keys are published only through the did:web document at
https://exo-trust.com/.well-known/did.json and never in this repository.
