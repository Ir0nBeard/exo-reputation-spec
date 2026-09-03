# Governance — EXO Reputation Spec

## Maintainers

This repository is maintained by the EXO Foundation (https://exo-trust.com),
the neutral body behind the EXO trust layer. It is a process-governed
standard: no individuals are named or identified in this repository, and all
maintainer actions are taken in a neutral-body capacity. The EXO reputation
layer is the Foundation's own first deployment of the standard — not its only
one.

## Status

- v0.1 (frozen 2026-08-21): schema semantics are final for this version.
- The addendum v0.1.1 (2026-08-25) is an additive semantic note; it changes
  no schema bytes.
- Roadmap items are non-normative and tracked as issues (see the Roadmap
  section of the spec).

## How changes are made

1. **Issue** — every change starts as an issue describing the problem and a
   concrete use case.
2. **Discussion** — maintainers and the community discuss the proposal in the
   issue thread.
3. **Pull request** — the PR references the issue and contains the change.
4. **Review and merge** — neutral-body maintainers review and merge. Merging
   is limited to maintainers; no individual contributor merges their own
   schema change.

## Version-bump rule

- A change to frozen v0.1 schema semantics — fields, types, constraints,
  EIP-712 structure, or type hashes — requires a **new version** published at
  a **new `$id` path** (for example `reputation-claim-v0.2.json`). The v0.1
  document and its `$id` are never mutated: they stay frozen and served.
- Backward-compatible additions land in a minor version (v0.2 for the first
  such change); breaking changes require a new major of 0.x with a migration
  note. Existing verifiers must keep accepting v0.1 envelopes.
- Editorial, documentation, URL, and process changes do not bump the schema
  version; they are recorded in CHANGELOG.md.

## Decision log

Schema-affecting decisions are recorded in CHANGELOG.md as dated entries with
a short rationale, so the standard's history is public and reviewable. This
is a standing rule: no schema-affecting decision is merged without a
corresponding log entry.

## Contribution license

All contributions are accepted under the MIT license (inbound = outbound —
the same license as this repository).

## Code of conduct

Be precise, be kind, no hype. Agents read the spec; humans read the issues.
Harassment, doxxing attempts, and astroturfing are not tolerated.

## Security

Report security issues privately — see SECURITY.md. Do not open public
issues for vulnerabilities.
