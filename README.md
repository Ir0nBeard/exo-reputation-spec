# EXO Reputation Spec

**Portable, verifiable reputation for AI agents.**

This repository is the open specification for EXO's reputation claim format —
a portable, tamper-evident, on-chain-committed reputation score that any
agent can carry to any marketplace, and that any EVM platform can verify
without integrating with us.

Status: **v0.1 draft** (frozen 2026-08-21, open for comment).

## What this is

The agent economy has a trust problem: anonymous programs transacting at
scale, with no neutral way to vet a counterparty. EXO's answer is a
reputation claim that is:

- **Portable** — an agent carries it as a signed EIP-712 claim; it works on
  any EVM platform with zero integration.
- **Verifiable** — signature check, on-chain commitment check, or full
  recomputation from chain events. Three trust tiers, verifier's choice.
- **Tamper-evident** — a rolling hash chain on Base (via EAS predeploys)
  means the oracle cannot rewrite history without detection.
- **Stage-invariant** — identical schema in the credits era and the EXO era;
  only the `settlementEra` field and stake units differ.
- **Settlement-agnostic** — reputation never requires paying in any
  particular currency. Trust is the product; the service is open.

## Repository layout

```
schema/reputation-claim-v0.1.json   JSON Schema (canonical field definitions)
spec/exo-reputation-eip712-v0.1.md  EIP-712 envelope + verification recipe
verifier/verify_claim.py            Standalone example verifier (Python)
LICENSE                             MIT
```

## Quick verification recipe (any EVM stack)

Given a carried claim envelope (claim + signature + commitment):

1. `verifyTypedData(domain, types, claim, signature)` → recovered issuer must
   equal the pinned oracle signer (did:web doc at
   `https://exo-trust.com/.well-known/did.json` or on-chain
   `authorizedSigner()`).
2. `now <= claim.expiresAt` and `claim.nonce > last-seen-nonce(agentId)`.
3. Read-only EAS call: latest attestation for `agentId` has
   `scoreHash == keccak256(abi.encode(claim))` and `issuedAt >= claim.issuedAt`.
4. Optional strongest: recompute the raw components from indexed chain events
   and ERC-8004 registration + x402 receipts; compare the composite.

See `spec/exo-reputation-eip712-v0.1.md` for the full recipe and domain
parameters (Base mainnet chainId 8453, EAS `0x4200...21` as
verifyingContract).

## Design principles

- Raw components travel with the composite score — a verifier that distrusts
  our weights can verify the components; one that trusts them verifies the
  composite in O(1).
- Subject is the agent identity (ERC-8004 agentId or DID), never the wallet — a
  fresh wallet cannot inherit a score.
- 7-day claim expiry + per-agent nonce + EIP-712 domain separation: no
  stale claims, no replays, cross-chain replay impossible.
- Sybil resistance: identity binding, age penalty, import cap,
  reputation-weighted vouches, permanent public slashes, time-weighted stake.

## Commenting / contributing

This is a living draft. Open an issue or PR for schema changes, additional
verifier implementations (viem, ethers, Solidity), or portability feedback.
See CONTRIBUTING.md.

## Related

- EXO project: https://exo-trust.com (project domain; the guild economy is the
  first customer of this spec, never its only one)
- ERC-8004 Identity Registry on Base: https://eips.ethereum.org/EIPS/eip-8004
  (permissionless on-chain identity anchor — registration, wallet binding)
- EAS: https://attest.org (on-chain commitment rail, predeployed on Base)

## License

MIT — the spec is open; the data moat is the accumulated reputation corpus.
