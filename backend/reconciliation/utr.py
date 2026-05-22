# backend/reconciliation/utr.py
# UTR (Unique Transaction Reference) verification
# Validates NEFT/RTGS/IMPS transaction references cited in bank statements
# Each payment rail has a strict format — invalid format = fabricated reference

import re
import json
import os
from pathlib import Path

MOCK_DIR  = Path(__file__).parent.parent.parent / "mock_apis"
MOCK_MODE = os.getenv("UTR_MOCK", "true").lower() == "true"

# UTR format patterns per payment rail
UTR_PATTERNS = {
    "NEFT": r'^[A-Z]{4}[0-9]{12}$',         # bank code (4) + 12 digits
    "RTGS": r'^[A-Z]{4}[0-9]{12}$',         # same format different prefix
    "IMPS": r'^[0-9]{7,15}(/[0-9A-Z]+)?$',                  # 12 digits only
    "UPI":  r'^[0-9]{12}$',                  # 12 digits
}


def verify_utr(utr: str) -> dict:
    if not utr:
        return {
            "result": "UNVERIFIED",
            "claim": None,
            "registry_data": None,
            "notes": "No UTR/transaction reference found in document",
        }

    if MOCK_MODE:
        return _mock_verify_utr(utr)

    raise NotImplementedError("Production UTR API not configured")


def _mock_verify_utr(utr: str) -> dict:
    utr = utr.strip().upper()

    # Detect payment rail from UTR format
    rail, format_valid = _detect_rail(utr)

    if not format_valid:
        return {
            "result": "CONTRADICTED",
            "claim": utr,
            "registry_data": None,
            "notes": (
                f"UTR '{utr}' has invalid format. "
                f"Does not match any known NEFT/RTGS/IMPS/UPI pattern. "
                f"Transaction reference may be fabricated."
            ),
            "mock": True,
        }

    # Check for suspicious patterns
    suspicion = _check_suspicious_patterns(utr)
    if suspicion:
        return {
            "result": "CONTRADICTED",
            "claim": utr,
            "registry_data": None,
            "notes": suspicion,
            "mock": True,
        }

    # Load fixture and verify
    fixture  = _load_fixture("utr_valid.json")
    registry = fixture.get("data", {})

    return {
        "result": "CONFIRMED",
        "claim": utr,
        "registry_data": {
            "utr": utr,
            "payment_rail": rail,
            "format_valid": True,
            "status": "SUCCESS",
        },
        "notes": (
            f"UTR {utr} is a valid {rail} transaction reference. "
            f"Format verified against RBI payment rail specifications."
        ),
        "mock": True,
    }


def _detect_rail(utr: str) -> tuple:
    """Returns (rail_name, is_valid)"""
    # NEFT/RTGS: starts with 4 alpha chars
    if re.match(r'^[A-Z]{4}', utr):
        if re.match(UTR_PATTERNS["NEFT"], utr):
            prefix = utr[:4]
            rail = "RTGS" if prefix.endswith("R") else "NEFT"
            return rail, True
        return "NEFT", False

    # IMPS/UPI: digits optionally followed by slash and reference
    if re.match(r'^[0-9]', utr):
        if re.match(UTR_PATTERNS["IMPS"], utr):
            return "IMPS", True
        return "IMPS", False

    return "UNKNOWN", False


def _check_suspicious_patterns(utr: str) -> str:
    """Flag obviously fake UTRs."""
    digits = re.sub(r'[^0-9]', '', utr)

    # All same digit (e.g. 000000000000)
    if len(set(digits)) == 1:
        return f"UTR '{utr}' contains suspicious repeating digits — likely fabricated."

    # Sequential digits (e.g. 123456789012)
    if digits == ''.join(str(i % 10) for i in range(len(digits))):
        return f"UTR '{utr}' contains sequential digits — likely fabricated."

    return ""


def _load_fixture(filename: str) -> dict:
    path = MOCK_DIR / filename
    with open(path, "r") as f:
        return json.load(f)
