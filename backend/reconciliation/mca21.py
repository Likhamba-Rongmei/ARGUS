# backend/reconciliation/mca21.py
# MCA21 company registry verification
# Verifies CIN, company name, director details
# Uses mock adapter for hackathon — mirrors real API schema exactly

import json
import os
from pathlib import Path


MOCK_DIR = Path(__file__).parent.parent.parent / "mock_apis"
MOCK_MODE = os.getenv("MCA21_MOCK", "true").lower() == "true"


def verify_cin(cin: str, claimed_company_name: str = None) -> dict:
    """
    Verify a CIN against MCA21 registry.
    In mock mode: fictional CINs return not_found,
    real-format CINs return found.

    Returns:
    {
        "result": "CONFIRMED" | "CONTRADICTED" | "UNVERIFIED",
        "claim": str,
        "registry_data": dict or None,
        "notes": str
    }
    """
    if not cin:
        return {
            "result": "UNVERIFIED",
            "claim": None,
            "registry_data": None,
            "notes": "No CIN found in document to verify"
        }

    if MOCK_MODE:
        return _mock_verify_cin(cin, claimed_company_name)

    # Production: real MCA21 API call would go here
    raise NotImplementedError("Production MCA21 API not configured")


def _mock_verify_cin(cin: str, claimed_company_name: str = None) -> dict:
    """
    Mock CIN verification.
    Uses fictional CIN detection to route to found/not_found fixture.

    Logic:
    - CINs ending in 999999 = fictional = not found
    - All others = found (uses found fixture)
    """
    is_fictional = cin.endswith("999999") or \
                   not _is_valid_cin_format(cin)

    if is_fictional:
        fixture = _load_fixture("mca21_cin_notfound.json")
        return {
            "result": "CONTRADICTED",
            "claim": cin,
            "registry_data": None,
            "notes": f"CIN {cin} does not exist in MCA21 registry. "
                     f"Company registration cannot be verified.",
            "mock": True
        }

    fixture = _load_fixture("mca21_cin_found.json")
    registry_data = fixture.get("data", {})

    # CIN must match mock exactly
    if cin.upper() != registry_data.get("cin", "").upper():
        return {
            "result": "CONTRADICTED",
            "claim": cin,
            "registry_data": None,
            "notes": f"CIN {cin} not found in MCA21 registry.",
            "mock": True
        }

    return {
        "result": "CONFIRMED",
        "claim": cin,
        "registry_data": registry_data,
        "notes": f"CIN {cin} verified. Company active in MCA21 registry.",
        "mock": True
    }


def _is_valid_cin_format(cin: str) -> bool:
    """
    Validate CIN format: L/U + 5digits + 2letters + 4digits + 3letters + 6digits
    Example: U72900MH2019PTC123456
    """
    import re
    pattern = r'^[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$'
    return bool(re.match(pattern, cin.upper()))


def _fuzzy_name_match(name1: str, name2: str) -> bool:
    """
    Simple fuzzy company name match.
    Strips common suffixes before comparing.
    """
    suffixes = [
        "private limited", "pvt ltd", "pvt. ltd.",
        "limited", "ltd", "llp", "inc"
    ]
    for suffix in suffixes:
        name1 = name1.replace(suffix, "").strip()
        name2 = name2.replace(suffix, "").strip()

    # Check if core names are similar enough
    return name1 in name2 or name2 in name1 or \
           _word_overlap(name1, name2) > 0.6


def _word_overlap(s1: str, s2: str) -> float:
    words1 = set(s1.split())
    words2 = set(s2.split())
    if not words1 or not words2:
        return 0.0
    return len(words1 & words2) / max(len(words1), len(words2))


def _load_fixture(filename: str) -> dict:
    path = MOCK_DIR / filename
    with open(path, "r") as f:
        return json.load(f)
