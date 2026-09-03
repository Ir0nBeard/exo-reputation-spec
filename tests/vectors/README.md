# Test vectors — signed example envelope

This directory ships the shared verification fixture promised by
CONTRIBUTING.md: a real, signed example claim envelope plus expected
verification results. Every verifier implementation must reproduce these
results against the pinned example issuer before it is listed as conformant.

## Contents

| File | Purpose |
|---|---|
| `envelope-v0.1-example.json` | A real signed claim envelope: the 29-field `EXOReputationClaim`, EIP-712 typed data (Base mainnet domain, chainId 8453), 7-day TTL, nonce 1, signed with a throwaway example key. |
| `expected-verification.txt` | Exact output of the reference verifier on the envelope at generation time (exit 0). |
| `expected-issuer.json` | The example issuer address to pin as `--expected-issuer` (public; the signing key itself is not published). |
| `self_test.py` | Evergreen self-test used by the CI workflow; also runnable locally. |

## How to verify

```bash
python3 verifier/verify_claim.py \
  tests/vectors/envelope-v0.1-example.json \
  --expected-issuer 0x17faA289CA5B3Fa4a88C630Eac069BDC530462ed
```

Expected: exit 0 and every check `PASS` (see `expected-verification.txt`).
The fixture is self-contained — verification requires only stock
`eth_account` (plus `eth-abi`, `eth-hash`, `jsonschema`) and the reference
verifier in this repository. No secrets or internal tooling are needed.

## What the example represents

An issued-but-not-yet-attested first claim for a fictional agent
(`8004:8453:...:example-agent-7f3ac9`). `prevCommitHash` is zero (genesis),
the EAS `schemaUID`/`attestationUID` are zero placeholders and
`commitmentBlock` is 0 — the example was never registered with the EAS
registry. `scoreHash` is real and recomputable: the
`keccak256(abi.encode(claim))` value that an on-chain attestation would
commit. All other field values are synthetic and illustrative, chosen within
schema bounds. The `issuer` is a throwaway example key — production issuers
are pinned via the did:web document, never trusted from the claim itself.

## Time-boundedness (7-day TTL)

Claims are valid for 7 days by spec (`expiresAt == issuedAt + 604800`), so a
static vector expires roughly 7 days after it is generated. The signature,
schema, and score-hash checks are time-independent and hold forever; the
wall-clock expiry check is the only one that lapses. `self_test.py` treats
that lapse as expected while still failing on any real regression (tampered
signature, wrong pin, schema drift, hash mismatch), which is how the CI
workflow stays green and truthful.

## Generating your own vector

Use any EIP-712 signer. Build the 29-field claim (see
`schema/reputation-claim-v0.1.json`), set `issuer` to your key's address and
`expiresAt = issuedAt + 604800`, then sign the typed data over the domain
below and wrap claim + signature + commitment into the envelope shape shown
in `spec/exo-reputation-eip712-v0.1.md`:

```json
{ "name": "EXO Reputation", "version": "0.1", "chainId": 8453,
  "verifyingContract": "0x4200000000000000000000000000000000000021" }
```

Verify your result with `--expected-issuer <your address>`.
