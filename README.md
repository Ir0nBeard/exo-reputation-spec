# EXO Reputation Spec

**Portable, verifiable reputation for AI agents.** An open standard for
carrying an agent's reputation as a signed EIP-712 claim envelope instead of
any single platform's internal score. Any EVM marketplace can verify a claim —
signature, on-chain commitment, or recomputation from raw components — with
zero integration.

- **Portable** — one envelope, any EVM platform.
- **Verifiable** — three trust tiers, verifier's choice: signature-only,
  on-chain commitment, recomputation.
- **Tamper-evident** — rolling hash-chain commitments on Base (EAS
  predeploys) make history rewrites detectable.
- **Stage- and settlement-agnostic** — one schema across eras and currencies.

**Status:** v0.1 draft — frozen 2026-08-21, open for comment. An additive
v0.1.1 addendum (2026-08-25) pins the on-chain identity anchor without
changing schema bytes. Schema semantics are frozen; process and docs remain
open through the issue tracker.

## Repository layout

```
schema/reputation-claim-v0.1.json   Canonical JSON Schema (29 fields)
spec/exo-reputation-eip712-v0.1.md  EIP-712 envelope + verification recipe
verifier/verify_claim.py            Reference verifier (stock eth_account)
tests/vectors/                      Signed example envelope + expected results
LICENSE                             MIT
```

## Verify a claim in four steps

1. Recover the issuer: `verifyTypedData(domain, types, claim, signature)`
   must equal the pinned signer (did:web at
   `https://exo-trust.com/.well-known/did.json` or on-chain
   `authorizedSigner()`).
2. Check `now <= expiresAt` and `nonce > last-seen-nonce(agentId)`.
3. Read-only EAS call: the latest attestation for `agentId` has
   `scoreHash == keccak256(abi.encode(claim))` and
   `issuedAt >= claim.issuedAt`.
4. Optional strongest tier: recompute components from indexed chain events,
   ERC-8004 registration, and x402 receipts.

```bash
python3 verifier/verify_claim.py \
  tests/vectors/envelope-v0.1-example.json \
  --expected-issuer <pinned issuer>
```

Domain parameters and the full recipe are in the spec (Base mainnet chainId
8453, EAS `0x4200...21` as `verifyingContract`).

## Governance

- GOVERNANCE.md — change process, version-bump rule, decision log
- CONTRIBUTING.md — how to contribute
- SECURITY.md — private disclosure
- CHANGELOG.md — version history (Keep a Changelog)

## Related standards

- ERC-8004 agent identity:
  https://github.com/ethereum/ERCs/blob/master/ERCS/erc-8004.md
- EAS (on-chain commitments): https://attest.org
- Canonical schema: https://exo-trust.com/schemas/reputation-claim-v0.1.json

## License

MIT
