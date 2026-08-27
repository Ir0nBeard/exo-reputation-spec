#!/usr/bin/env python3
"""EXO Reputation Spec — standalone example verifier (v0.1).

Verifies a carried reputation claim envelope with ZERO integration: stock
eth_account, no EXO SDK. This is the exact recipe a third-party marketplace
runs to check "is this counterparty trustworthy?" — trust tier 1
(signature) and the score-hash integrity check.

Dependencies: eth-account, eth-abi, eth-hash, jsonschema
(pip install eth-account eth-abi jsonschema)

Usage:
    python3 verify_claim.py envelope.json --expected-issuer 0x...
    python3 verify_claim.py envelope.json --expected-issuer=0x...

The --expected-issuer pin is REQUIRED (refuses to run unpinned): an issuer
must always be pinned to the did:web / authorizedSigner address, otherwise
any self-signed claim by any key would "verify".

Envelope format (what GET /v1/reputation/{agent_id} returns):
    {
      "schema": "exo.reputation/claim/v0.1",
      "claim": { ...29 fields... },
      "signature": {"r": "0x...", "s": "0x...", "v": 27},
      "commitment": {"chainId": 8453, "easSchemaUID": "...",
                     "attestationUID": "...", "scoreHash": "0x..."}
    }

Exit 0 = verified, nonzero = failed. Prints a human-readable verdict.
Never raises a traceback on hostile input: every malformed envelope yields
a structured FAIL and exit 1.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from eth_account import Account
from eth_account.messages import encode_typed_data

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

DOMAIN = {
    "name": "EXO Reputation",
    "version": "0.1",
    "chainId": 8453,  # Base mainnet (84532 = Base Sepolia)
    "verifyingContract": "0x4200000000000000000000000000000000000021",  # EAS
}

CLAIM_TYPES: Dict[str, List[Dict[str, str]]] = {
    "EXOReputationClaim": [
        {"name": "schemaVersion", "type": "string"},
        {"name": "claimId", "type": "bytes32"},
        {"name": "agentId", "type": "string"},
        {"name": "agentWallet", "type": "address"},
        {"name": "issuer", "type": "address"},
        {"name": "issuedAt", "type": "uint256"},
        {"name": "expiresAt", "type": "uint256"},
        {"name": "commitmentBlock", "type": "uint256"},
        {"name": "prevCommitHash", "type": "bytes32"},
        {"name": "formulaVersion", "type": "string"},
        {"name": "weightsRef", "type": "string"},
        {"name": "settlementEra", "type": "string"},
        {"name": "compositeScore", "type": "uint256"},
        {"name": "identityKarma", "type": "uint256"},
        {"name": "identityClaimed", "type": "bool"},
        {"name": "identityOwnerXVerified", "type": "bool"},
        {"name": "identityImportCapped", "type": "bool"},
        {"name": "identitySnapshotHash", "type": "bytes32"},
        {"name": "stakeTimeWeighted", "type": "uint256"},
        {"name": "stakeCurrent", "type": "uint256"},
        {"name": "taskCompleted", "type": "uint256"},
        {"name": "taskFailed", "type": "uint256"},
        {"name": "vouchCount", "type": "uint256"},
        {"name": "vouchWeightedSum", "type": "uint256"},
        {"name": "slashCount", "type": "uint256"},
        {"name": "slashSeverityTotal", "type": "uint256"},
        {"name": "accountAgeDays", "type": "uint256"},
        {"name": "activeDays", "type": "uint256"},
        {"name": "nonce", "type": "uint256"},
    ]
}

FIELD_ORDER = [f["name"] for f in CLAIM_TYPES["EXOReputationClaim"]]
SOLIDITY_TYPES = [
    "string", "bytes32", "string", "address", "address", "uint256",
    "uint256", "uint256", "bytes32", "string", "string", "string",
    "uint256", "uint256", "bool", "bool", "bool", "bytes32",
    "uint256", "uint256", "uint256", "uint256", "uint256", "uint256",
    "uint256", "uint256", "uint256", "uint256", "uint256",
]

# Frozen spec semantic constants (docs/EXO_REPUTATION_EIP712_v0.1.md)
CLAIM_TTL_SECONDS = 604800        # expiresAt == issuedAt + 7 days
MAX_COMPOSITE_SCORE = 10000       # 0-10,000 basis points
MAX_ISSUED_AT_SKEW = 3600         # issuedAt more than 1h in the future = absurd

# secp256k1 group order n; canonical signatures require s <= n/2 (low-s)
SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" \
    / "reputation-claim-v0.1.json"
CLAIM_SCHEMA = json.loads(_SCHEMA_PATH.read_text())


def score_hash(claim: Dict[str, Any]) -> bytes:
    """keccak256(abi.encode(claim fields in struct order))."""
    from eth_abi import encode
    from eth_hash.auto import keccak

    def norm(v: Any, t: str, field: str) -> Any:
        if t == "bytes32":
            return bytes.fromhex(v[2:]) if isinstance(v, str) else v
        if t == "bool":
            # STRICT: a bool field must be a real bool. "false"/"true"/0/1
            # strings silently coerce truthily and would sign as True — reject.
            if not isinstance(v, bool):
                raise ValueError(
                    f"claim field {field!r} must be a real boolean "
                    f"(True/False), got {type(v).__name__}: {v!r}")
            return v
        return v

    values = [norm(claim[f], t, f) for f, t in zip(FIELD_ORDER, SOLIDITY_TYPES)]
    return keccak(encode(SOLIDITY_TYPES, values))


def validate_claim_schema(claim: Any) -> List[str]:
    """Validate the claim against the published JSON Schema. Returns error
    strings (empty = valid). Catches extra fields (additionalProperties:
    false), consts, enums, type/pattern/bounds violations."""
    if jsonschema is None:
        return ["jsonschema not installed — cannot validate claim "
                "(pip install jsonschema)"]
    if not isinstance(claim, dict):
        return [f"claim is not an object (got {type(claim).__name__})"]
    try:
        jsonschema.validate(instance=claim, schema=CLAIM_SCHEMA)
        return []
    except jsonschema.ValidationError as e:
        path = "/".join(str(p) for p in e.path) or "root"
        return [f"schema violation at {path}: {e.message}"]


def validate_claim_semantics(claim: Dict[str, Any]) -> List[str]:
    """Spec semantic rules not expressible in the JSON Schema. Returns error
    strings (empty = valid)."""
    errs: List[str] = []
    # compositeScore in [0, 10000]
    try:
        score = int(claim.get("compositeScore", -1))
        if not (0 <= score <= MAX_COMPOSITE_SCORE):
            errs.append(f"compositeScore {score} out of "
                        f"[0, {MAX_COMPOSITE_SCORE}]")
    except (TypeError, ValueError):
        errs.append("compositeScore is not an integer")
    # expiresAt == issuedAt + 604800
    issued = None
    try:
        issued = int(claim.get("issuedAt", -1))
        exp = int(claim.get("expiresAt", -1))
        if exp != issued + CLAIM_TTL_SECONDS:
            errs.append(f"expiresAt {exp} != issuedAt {issued} + "
                        f"{CLAIM_TTL_SECONDS} (7-day TTL)")
    except (TypeError, ValueError):
        errs.append("issuedAt/expiresAt are not integers")
    # issuedAt not absurdly in the future
    if issued is not None and issued > int(time.time()) + MAX_ISSUED_AT_SKEW:
        errs.append(f"issuedAt {issued} is absurdly in the future "
                    f"(> {MAX_ISSUED_AT_SKEW}s skew allowed)")
    return errs


def verify_envelope(envelope: Dict[str, Any],
                    expected_issuer: str) -> List[Tuple[str, str]]:
    """Returns a list of (status, message) tuples. All must be PASS.

    Never raises on hostile input: structural, schema, semantic, signature
    and hash problems all become FAIL entries."""
    checks: List[Tuple[str, str]] = []
    claim = envelope.get("claim")
    sig = envelope.get("signature")

    # 1. Structural — envelope/claim/signature shapes
    if not isinstance(claim, dict):
        checks.append(("FAIL", f"claim is not an object "
                               f"(got {type(claim).__name__})"))
        return checks
    if not isinstance(sig, dict):
        checks.append(("FAIL", "signature is not an object"))
        return checks
    missing = [f for f in FIELD_ORDER if f not in claim]
    checks.append(("PASS" if not missing else "FAIL",
                   f"schema: all {len(FIELD_ORDER)} fields present"
                   + (f" (missing: {missing})" if missing else "")))

    # 2. JSON Schema + semantic bounds (H3: pinned but sane)
    for err in validate_claim_schema(claim):
        checks.append(("FAIL", err))
    for err in validate_claim_semantics(claim):
        checks.append(("FAIL", err))

    # 3. Signature recovery (trust tier 1) — canonical form first (M1)
    try:
        r_hex, s_hex, v = sig["r"], sig["s"], sig["v"]
        if not (isinstance(r_hex, str) and isinstance(s_hex, str)):
            raise ValueError("r and s must be hex strings")
        if not isinstance(v, int) or isinstance(v, bool):
            raise ValueError(f"v must be an integer, got {type(v).__name__}")
        if v not in (27, 28):
            raise ValueError(f"v={v} not in {{27, 28}} (non-canonical)")
        r = bytes.fromhex(r_hex[2:] if r_hex.startswith("0x") else r_hex)
        s = bytes.fromhex(s_hex[2:] if s_hex.startswith("0x") else s_hex)
        if len(r) != 32 or len(s) != 32:
            raise ValueError(f"r/s must be 32 bytes, got "
                             f"{len(r)}/{len(s)}")
        if int.from_bytes(s, "big") > SECP256K1_N // 2:
            raise ValueError("s > n/2 (high-s malleated signature "
                             "— non-canonical)")
        typed = encode_typed_data(full_message={
            "domain": DOMAIN, "types": CLAIM_TYPES, "message": claim})
        sig_bytes = r + s + bytes([v])
        recovered = Account.recover_message(typed, signature=sig_bytes)
    except Exception as e:  # any malformed signature -> structured FAIL
        checks.append(("FAIL", f"signature invalid: {e}"))
        return checks
    issuer_ok = recovered.lower() == str(claim.get("issuer", "")).lower()
    checks.append(("PASS" if issuer_ok else "FAIL",
                   f"signature: recovered issuer {recovered}"))

    # 4. Expected issuer pin (required — H2)
    pin_ok = recovered.lower() == expected_issuer.lower()
    checks.append(("PASS" if pin_ok else "FAIL",
                   f"pinned issuer match ({expected_issuer})"))

    # 5. Expiry
    try:
        now = int(time.time())
        exp = int(claim.get("expiresAt", 0))
        checks.append(("PASS" if now <= exp else "FAIL",
                       f"not expired (now {now} <= expiresAt {exp})"))
    except (TypeError, ValueError):
        checks.append(("FAIL", "expiresAt is not an integer"))

    # 6. Score-hash integrity (commitment match)
    try:
        comm_hash = envelope.get("commitment", {}).get("scoreHash", "")
        sh = score_hash(claim)
        hash_ok = str(comm_hash).lower() == ("0x" + sh.hex()).lower()
        checks.append(("PASS" if hash_ok else "FAIL",
                       "scoreHash matches recomputed "
                       "keccak(abi.encode(claim))"))
    except Exception as e:
        checks.append(("FAIL", f"scoreHash check failed: {e}"))

    # 7. Domain separation sanity
    cd = envelope.get("commitment", {}).get("chainId")
    checks.append(("PASS" if cd == DOMAIN["chainId"] else "FAIL",
                   f"commitment chainId {cd} == domain chainId "
                   f"{DOMAIN['chainId']}"))

    return checks


class _Parser(argparse.ArgumentParser):
    """argparse that exits 1 (not 2) on usage errors — loud, script-friendly."""

    def error(self, message: str) -> None:  # type: ignore[override]
        self.print_usage(sys.stderr)
        print(f"error: {message}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    ap = _Parser(description="EXO reputation claim verifier (tier 1)")
    ap.add_argument("envelope", help="path to the claim envelope JSON")
    ap.add_argument("--expected-issuer", required=True, metavar="0xADDR",
                    help="REQUIRED: pinned oracle signer address "
                         "(did:web / authorizedSigner) — refuses to "
                         "verify unpinned")
    args = ap.parse_args()

    expected = args.expected_issuer
    if not (isinstance(expected, str) and expected.startswith("0x")
            and len(expected) == 42):
        print(f"[FAIL] --expected-issuer must be a 0x-prefixed address "
              f"(40 hex chars), got {expected!r}")
        sys.exit(1)

    try:
        envelope = json.load(open(args.envelope))
    except Exception as e:
        print(f"[FAIL] cannot read envelope {args.envelope}: {e}")
        sys.exit(1)
    if not isinstance(envelope, dict):
        print("[FAIL] envelope is not a JSON object")
        sys.exit(1)

    try:
        checks = verify_envelope(envelope, expected)
    except Exception as e:  # belt-and-suspenders: NEVER a traceback
        print(f"[FAIL] verifier error: {e}")
        sys.exit(1)

    all_pass = True
    for status, msg in checks:
        print(f"  [{status}] {msg}")
        all_pass = all_pass and status == "PASS"

    print()
    if all_pass:
        print("VERIFIED — claim is valid (tier 1: signature + integrity).")
        print("For tier 2, check the on-chain EAS commitment "
              "(see spec section 5).")
        sys.exit(0)
    print("NOT VERIFIED — see failed checks above.")
    sys.exit(1)


if __name__ == "__main__":
    main()
