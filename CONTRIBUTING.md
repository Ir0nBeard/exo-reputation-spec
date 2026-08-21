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
   Solidity, Go, Rust. Each verifier must pass the same envelope fixture.
3. **Portability feedback** — you run a marketplace and tried to verify a
   claim: what was hard? What would make adoption easier?
4. **Documentation** — typos, unclear steps, missing edge cases.

## Process

- Open an issue before a large PR (schema changes especially — the schema is
  the contract; changes bump the version).
- v0.1 is frozen for the current pilot. Proposed changes target v0.2 and must
  be backward-compatible with v0.1 envelopes (a v0.1 verifier must keep
  working) unless the change is explicitly a breaking-version bump with a
  migration note.
- All contributions under the MIT license.

## Verification fixture

A signed example envelope will be published here for verifier cross-testing.
Until then, generate one with the EXO signing tooling or ask for a sample.

## Code of conduct

Be precise, be kind, no hype. Agents read the spec; humans read the issues.
