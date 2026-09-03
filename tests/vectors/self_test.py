#!/usr/bin/env python3
"""Evergreen CI self-test for the shipped test vector.

Runs the reference verifier (verifier/verify_claim.py) against the example
envelope in this directory and enforces that EVERY check passes except the
wall-clock expiry check.

Why: claims are valid for 7 days by spec (expiresAt == issuedAt + 604800), so
a static vector expires about 7 days after generation. The signature, schema,
pinned-issuer, and score-hash checks are time-independent and must pass
forever; only "not expired" is expected to lapse. Any other failure (tampered
signature, wrong issuer, schema drift, hash mismatch, structural break) fails
the job.

Usage:
    python3 tests/vectors/self_test.py

Exit 0 = fixture valid (modulo its documented TTL); nonzero = regression.
"""

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]  # repo root
VECTOR = ROOT / "tests" / "vectors" / "envelope-v0.1-example.json"
VERIFIER = ROOT / "verifier" / "verify_claim.py"

# The verifier refuses to run unpinned; pin to the issuer carried in the
# fixture itself (it is the documented example issuer, expected-issuer.json).
EXPECTED_ISSUER = (
    "0x17faA289CA5B3Fa4a88C630Eac069BDC530462ed"
)


def main() -> int:
    if not VECTOR.exists():
        print(f"[FAIL] missing fixture: {VECTOR}")
        return 1
    envelope = json.loads(VECTOR.read_text())
    issuer = envelope.get("claim", {}).get("issuer")
    if issuer is None:
        print("[FAIL] fixture has no claim.issuer")
        return 1

    proc = subprocess.run(
        [sys.executable, str(VERIFIER), str(VECTOR),
         "--expected-issuer", EXPECTED_ISSUER],
        capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    print(out)

    fails = [ln for ln in out.splitlines() if "[FAIL]" in ln]
    # Tolerate only the wall-clock expiry lapse of the static vector.
    unacceptable = [ln for ln in fails if "not expired" not in ln]
    if unacceptable:
        print("SELF-TEST FAIL — unacceptable verifier failures:")
        for ln in unacceptable:
            print(" ", ln)
        return 1
    if fails:
        print("NOTE: the only failing check is the wall-clock expiry of the "
              "static vector (7-day TTL by spec) — expected once the vector "
              "ages. Signature, schema, pin, and hash integrity all pass "
              "above.")
    if proc.returncode == 0 or (fails and not unacceptable):
        print("SELF-TEST PASS")
        return 0
    print("SELF-TEST FAIL — unexpected verifier exit "
          f"code {proc.returncode}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
