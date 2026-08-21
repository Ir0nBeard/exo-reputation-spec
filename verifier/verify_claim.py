#!/usr/bin/env python3
"""EXO Reputation Spec — standalone example verifier (v0.1).

Verifies a carried reputation claim envelope with ZERO integration: stock
eth_account, no EXO SDK. This is the exact recipe a third-party marketplace
runs to check "is this counterparty trustworthy?" — trust tier 1
(signature) and the score-hash integrity check.

Dependencies: eth-account, eth-abi, eth-hash (pip install eth-account eth-abi)

Usage:
    python3 verify_claim.py envelope.json [--expected-issuer 0x...]

Envelope format (what GET /v1/reputation/{agent_id} returns):
    {
      "schema": "exo.reputation/claim/v0.1",
      "claim": { ...29 fields... },
      "signature": {"r": "0x...", "s": "0x...", "v": 27},
      "commitment": {"chainId": 8453, "easSchemaUID": "...",
                     "attestationUID": "...", "scoreHash": "0x..."}
    }

Exit 0 = verified, nonzero = failed. Prints a human-readable verdict.
"""

import json
import sys
from typing import Any, Dict, List, Optional

from eth_account import Account
from eth_account.messages import encode_typed_data

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


def score_hash(claim: Dict[str, Any]) -> bytes:
    """keccak256(abi.encode(claim fields in struct order))."""
    from eth_abi import encode
    from eth_hash.auto import keccak

    def norm(v: Any, t: str) -> Any:
        if t == "bytes32":
            return bytes.fromhex(v[2:]) if isinstance(v, str) else v
        if t == "bool":
            return bool(v)
        return v

    values = [norm(claim[f], t) for f, t in zip(FIELD_ORDER, SOLIDITY_TYPES)]
    return keccak(encode(SOLIDITY_TYPES, values))


def verify_envelope(envelope: Dict[str, Any],
                    expected_issuer: Optional[str] = None) -> List[str]:
    """Returns a list of (pass, message) tuples. All must pass."""
    checks: List[str] = []
    claim = envelope.get("claim", {})
    sig = envelope.get("signature", {})

    # 1. Structural
    missing = [f for f in FIELD_ORDER if f not in claim]
    checks.append(("PASS" if not missing else "FAIL",
                   f"schema: all {len(FIELD_ORDER)} fields present"
                   + (f" (missing: {missing})" if missing else "")))

    # 2. Signature recovery (trust tier 1)
    typed = encode_typed_data(full_message={
        "domain": DOMAIN, "types": CLAIM_TYPES, "message": claim})
    sig_bytes = (bytes.fromhex(sig["r"][2:]) + bytes.fromhex(sig["s"][2:])
                 + bytes([sig["v"]]))
    recovered = Account.recover_message(typed, signature=sig_bytes)
    issuer_ok = recovered.lower() == claim.get("issuer", "").lower()
    checks.append(("PASS" if issuer_ok else "FAIL",
                   f"signature: recovered issuer {recovered}"))

    # 3. Expected issuer (if caller pinned one — e.g. from did:web doc)
    if expected_issuer:
        pin_ok = recovered.lower() == expected_issuer.lower()
        checks.append(("PASS" if pin_ok else "FAIL",
                       f"pinned issuer match ({expected_issuer})"))

    # 4. Expiry
    import time
    now = int(time.time())
    exp = int(claim.get("expiresAt", 0))
    checks.append(("PASS" if now <= exp else "FAIL",
                   f"not expired (now {now} <= expiresAt {exp})"))

    # 5. Score-hash integrity (commitment match)
    comm_hash = envelope.get("commitment", {}).get("scoreHash", "")
    sh = score_hash(claim)
    hash_ok = comm_hash.lower() == ("0x" + sh.hex()).lower()
    checks.append(("PASS" if hash_ok else "FAIL",
                   "scoreHash matches recomputed keccak(abi.encode(claim))"))

    # 6. Domain separation sanity
    cd = envelope.get("commitment", {}).get("chainId")
    checks.append(("PASS" if cd == DOMAIN["chainId"] else "FAIL",
                   f"commitment chainId {cd} == domain chainId "
                   f"{DOMAIN['chainId']}"))

    return checks


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    envelope = json.load(open(sys.argv[1]))
    expected = sys.argv[2].split("=")[1] if len(sys.argv) > 2 and \
        sys.argv[2].startswith("--expected-issuer=") else None

    checks = verify_envelope(envelope, expected)
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
