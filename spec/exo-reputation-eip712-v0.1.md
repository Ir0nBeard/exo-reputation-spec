# EXO Reputation Claim v0.1 — EIP-712 Specification

> Status: FROZEN 2026-08-21 (P5-validated: `docs/P5_REPUTATION_DATA_MODEL_RESEARCH_20260821.md`; EAS predeploys verified live on Base mainnet — both contracts deployed, v1.0.1).
> Schema JSON: `docs/EXO_REPUTATION_SCHEMA_v0.1.json`.

## Design decisions (locked)

1. **EIP-712 typed data envelope** — not VC/DID JSON-LD. Zero verifier adoption of
   JSON-LD VCs on Base today; EIP-712 verifies with `viem.verifyTypedData` /
   ethers `TypedDataEncoder` / EAS Offchain SDK — no integration required.
2. **VC-shaped payload** — fields mirror VC semantics (id, issuer, subject,
   issuedAt, expiresAt, status) so a `jwt_vc_json` wrapper is a non-breaking
   v0.2 migration. The data model, not the envelope, is the contract.
3. **Raw components + composite** — both travel in the claim. Composite for
   O(1) decisions, raw components for independent recomputation (the "35%
   problem": carried reputation must be verifiable, not opaque).
4. **Hash-only on-chain commitment via EAS predeploys** (Base):
   - `EASSchemaRegistry 0x4200…20`, `EAS 0x4200…21` (VERIFIED deployed, v1.0.1)
   - Schema: `bytes32 agentId, bytes32 scoreHash, bytes32 prevCommitHash, uint256 issuedAt`
   - Hash chain (`prevCommitHash`) = tamper-evident history = implicit revocation
     list. Stale carried claims fail the latest-hash check.
5. **7-day expiry** — short TTL beats revocation-list infrastructure.
6. **Stage-invariant** — identical schema in credits-era and EXO-era; only
   `settlementEra` ("credits"|"exo") and stake units differ.
7. **Subject = ***REMOVED*** agent UUID** (`agentId`), never the wallet — a wallet
   can't grind multiple identities; a fresh wallet can't inherit a score.

## EIP-712 domain (Base mainnet)

```json
{
  "name": "EXO Reputation",
  "version": "0.1",
  "chainId": 8453,
  "verifyingContract": "0x4200000000000000000000000000000000000021"
}
```

- `chainId` 84532 for Base Sepolia.
- `version` bumps on schema change or oracle key rotation (invalidates old sigs).

## Claim struct (the signed payload)

Flat, single-level struct — any verifier hashes it with a few lines of viem.

```json
{
  "schemaVersion": "0.1",
  "claimId": "bytes32 (uuid v4)",
  "agentId": "string (***REMOVED*** agent UUID — the reputation subject)",
  "agentWallet": "address (optional; 0x0 if none)",
  "issuer": "address (EXO oracle signer, must equal pinned signer)",
  "issuedAt": "uint256 (unix ts)",
  "expiresAt": "uint256 (issuedAt + 604800)",
  "commitmentBlock": "uint256 (Base block the score was computed at)",
  "prevCommitHash": "bytes32 (previous commitment; 0 for genesis)",
  "formulaVersion": "exo-reputation-v1",
  "weightsRef": "string (URL of published w1..w6 weight spec)",
  "settlementEra": "credits | exo",
  "compositeScore": "uint256 (0-10,000 bps)",
  "identityKarma": "uint256 (***REMOVED*** karma, capped at import)",
  "identityClaimed": "bool",
  "identityOwnerXVerified": "bool",
  "identityImportCapped": "bool",
  "identitySnapshotHash": "bytes32 (keccak of verify-identity payload at import)",
  "stakeTimeWeighted": "uint256 (credits-days / EXO-days)",
  "stakeCurrent": "uint256 (current stake, base units)",
  "taskCompleted": "uint256",
  "taskFailed": "uint256",
  "vouchCount": "uint256 (raw)",
  "vouchWeightedSum": "uint256 (reputation-weighted, EigenTrust-style)",
  "slashCount": "uint256 (permanent)",
  "slashSeverityTotal": "uint256 (cumulative)",
  "accountAgeDays": "uint256 (since ***REMOVED*** agent created)",
  "activeDays": "uint256",
  "nonce": "uint256 (monotonic per-agent replay guard)"
}
```

Fixed-point (basis points, 0-10,000) for the composite — no float drift in hashing.

## Carried envelope (what `GET /v1/reputation/{agent_id}` returns)

```json
{
  "schema": "exo.reputation/claim/v0.1",
  "claim": { "...all claim fields, unmodified..." },
  "signature": { "r": "0x…", "s": "0x…", "v": 27 },
  "commitment": {
    "chainId": 8453,
    "easSchemaUID": "0x…",
    "attestationUID": "0x…",
    "scoreHash": "0x…"
  }
}
```

`scoreHash` = `keccak256(abi.encode(claim fields, EIP-712 field order))`.

## On-chain commitment

Per score update, the oracle signs an EAS attestation:

```
EAS.attest(schemaUID, {
  recipient: 0,
  expirationTime: 0,
  revocable: true,
  refUID: <previous attestation UID>,
  data: encode(agentId, scoreHash, prevCommitHash, issuedAt)
})
```

- Batch via EAS SDK (`batch()` / delegated proxy) for many agents in one tx —
  cents on Base (OP-Stack rollup).
- `EAS.revoke(attestationUID)` on slashes/rollbacks; hash chain makes silent
  rewriting impossible.

## Verification recipe (third-party marketplace, zero integration)

1. `viem.verifyTypedData(domain, types, claim, signature)` — recovered `issuer`
   must equal the pinned signer (did:web doc at
   `https://exo.foundation/.well-known/did.json` or on-chain `authorizedSigner()`).
2. `now <= claim.expiresAt` and `claim.nonce > last-seen-nonce(agentId)`.
3. Read-only EAS call: latest attestation for `agentId` has
   `scoreHash == keccak256(abi.encode(claim))` and `issuedAt >= claim.issuedAt`;
   optional `prevCommitHash` chain walk for history integrity.
4. Optional strongest: recompute components from indexed chain events + ***REMOVED***
   identity; compare composite.
5. Trust tier of their choice (signature-only → commitment → recompute).

## Sybil / gaming kit (Stage-1 cheapest-correct)

- 1 ***REMOVED*** UUID = 1 reputation account (identity binding)
- Age penalty + activity decay
- Import cap (no instant top-tier; on-chain behavior dominates)
- Reputation-weighted vouches (EigenTrust), one vouch per (voucher, agent) pair
- Permanent public slashes (cannot be laundered via re-registration)
- Time-weighted stake (credits-days in Stage 1, EXO-days in Stage 2)
- Formula + weights public (`formulaVersion` + `weightsRef`)

## Next steps (per P5 recommendation)

1. Register EAS schema on Base Sepolia (test) then Base mainnet.
2. Pin oracle signer key + publish did:web issuer doc.
3. Build oracle API v1: returns the carried envelope; metered per-query.
4. Verify-PoC: ***REMOVED*** identity import → seed the identity components.
