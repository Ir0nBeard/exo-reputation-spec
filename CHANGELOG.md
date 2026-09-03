# Changelog

All notable changes to the EXO Reputation Spec are documented here. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project uses 0.x versions: a minor bump (v0.2) is a new, possibly
breaking schema version published at a new `$id` path — v0.1 stays frozen and
served unchanged (see GOVERNANCE.md).

## [Unreleased]

### Added

- Packaging round (2026-09-03): neutral-voice README; GOVERNANCE.md,
  SECURITY.md, and this CHANGELOG; a signed example envelope plus expected
  verification results under `tests/vectors/` with an evergreen CI self-test;
  issue templates for schema changes, bugs, and portability feedback; a
  JSON-Schema validation workflow.
- Editorial: the spec's "Next steps" section is now "Roadmap
  (non-normative)"; the did:web issuer publication is stated as a
  prerequisite for third parties; mainnet vs testnet domains are made
  explicit; the ERC-8004 link now points at the canonical ethereum/ERCs
  file.

## [v0.1.1] — 2026-08-25 — Addendum: on-chain identity anchor

### Added

- Addendum v0.1.1 (semantic note; no schema bytes change): the identity
  anchor is the ERC-8004 Identity Registry on Base mainnet plus the
  agent-owned wallet (did:pkh). `agentId` carries an ERC-8004 identity
  reference; all no-import identity values remain valid.
- Reference verifier hardening: canonical-signature checks (low-s, `v` in
  {27, 28}), required issuer pinning, score-hash integrity check.

### Changed

- did:web and project links pinned to the live domain (exo-trust.com);
  editorial cleanup of the next-steps section.

## [v0.1] — 2026-08-21 — Initial frozen draft

### Added

- EIP-712 claim envelope: the 29-field `EXOReputationClaim` struct, Base
  mainnet domain (chainId 8453, EAS `0x4200...21` as `verifyingContract`),
  7-day TTL, per-agent monotonic nonce.
- Canonical JSON Schema (`schema/reputation-claim-v0.1.json`), the reference
  verifier (`verifier/verify_claim.py`), and the verification recipe with
  three trust tiers (signature, on-chain commitment, recomputation).
