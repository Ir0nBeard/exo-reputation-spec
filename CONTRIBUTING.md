# Contributing to the EXO Reputation Spec

The spec is a living draft. The goal is an open standard that any agent
marketplace can adopt — so the fastest path to adoption is honest,
low-friction contribution.

## Ways to contribute

1. **Schema feedback** — open an issue on `schema/reputation-claim-v0.1.json`.
   Missing fields? Wrong types? A component that should be raw instead of
   computed? Say so with a concrete use case.
2. **Verifier implementations** — the recipe in
   `spec/exo-reputation-eip712-v0.1.md` is language-agnostic. We accept
   verifier implementations in other stacks: viem/TypeScript, ethers,
   Solidity, Go, Rust. Each verifier must pass the shared fixture in
   `tests/vectors/` (see its README for the expected results and for how to
   generate additional vectors with your own key).
3. **Portability feedback** — you run a marketplace and tried to verify a
   claim: what was hard? What would make adoption easier?
4. **Documentation** — typos, unclear steps, missing edge cases.

## Process

- Open an issue before a large PR (schema changes especially — the schema is
  the contract; changes bump the version).
- v0.1 is frozen for the current pilot. Proposed changes target v0.2 and must
  be backward-compatible with v0.1 envelopes (a v0.1 verifier must keep
  working) unless the change is explicitly a breaking-version bump with a
  migration note. Accepted schema changes ship at a **new `$id` path**; the
  v0.1 `$id` is never mutated (see GOVERNANCE.md).
- All contributions are licensed under the MIT license (inbound = outbound).

## Verification fixture

`tests/vectors/` ships a signed example envelope plus the expected
verification results — the shared fixture every verifier implementation must
reproduce. The fixture is self-contained: verifying it requires only stock
`eth_account` (or the equivalent in your stack) and the recipe in the spec.
See `tests/vectors/README.md`.

## AI-generated contributions

Contributions written with AI assistance are welcome, but are triaged and
merged only by human maintainers. AI agents should not open issues or pull
requests directly on this repository: route agent-generated material through
a human who takes responsibility for it. Automated or bulk submissions are
not accepted.

## Code of conduct

Be precise, be kind, no hype. Agents read the spec; humans read the issues.
