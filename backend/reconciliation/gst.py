# backend/reconciliation/gst.py
# GST Public API verification
# Verifies GSTIN validity and turnover against declared income
# Uses mock adapter for hackathon

import json
import os
import re
from pathlib import Path


MOCK_DIR  = Path(__file__).parent.parent.parent / "mock_apis"
MOCK_MODE = os.getenv("GST_MOCK", "true").lower() == "true"


# Turnover slab ranges in INR for comparison
TURNOVER_SLABS = {
    "Rs. Below 20 Lakhs":          (0,          2_000_000),
    "Rs. 20 Lakhs to Rs. 1 Crore": (2_000_000,  10_000_000),
    "Rs. 1 Crore to Rs. 5 Crore":  (10_000_000, 50_000_000),
    "Rs. 5 Crore to Rs. 25 Crore": (50_000_000, 250_000_000),
    "Rs. Above 25 Crore":          (250_000_000, float("inf")),
}


def verify_gstin(
    gstin: str,
    declared_revenue: float = None
) -> dict:
    """
    Verify GSTIN and cross-check declared revenue against turnover slab.

    Returns:
    {
        "result": "CONFIRMED" | "CONTRADICTED" | "UNVERIFIED",
        "claim": str,
        "registry_data": dict or None,
        "notes": str
    }
    """
    if not gstin:
        return {
            "result": "UNVERIFIED",
            "claim": None,
            "registry_data": None,
            "notes": "No GSTIN found in document to verify"
        }

    if MOCK_MODE:
        return _mock_verify_gstin(gstin, declared_revenue)

    raise NotImplementedError("Production GST API not configured")


def _mock_verify_gstin(
    gstin: str,
    declared_revenue: float = None
) -> dict:
    """
    Mock GSTIN verification.
    Checks format validity first.
    If declared_revenue provided, checks against turnover slab.
    """
    # GSTIN must match mock exactly
    fixture = _load_fixture("gst_valid_match.json")
    registry_data = fixture.get("data", {})
    if gstin.upper() != registry_data.get("gstin", "").upper():
        return {
            "result": "CONTRADICTED",
            "claim": gstin,
            "registry_data": None,
            "notes": f"GSTIN {gstin} not found in GST registry.",
            "mock": True
        }

    # If revenue declared, check if it fits the turnover slab
    if declared_revenue:
        fixture = _load_fixture("gst_valid_match.json")
        registry_data = fixture.get("data", {})
        slab = registry_data.get("turnover_slab", "")

        slab_match = _check_revenue_in_slab(declared_revenue, slab)

        if not slab_match:
            # Load mismatch fixture for realistic response
            mismatch_fixture = _load_fixture("gst_valid_mismatch.json")
            mismatch_data    = mismatch_fixture.get("data", {})
            return {
                "result": "CONTRADICTED",
                "claim": gstin,
                "registry_data": mismatch_data,
                "notes": (
                    f"Revenue mismatch: declared Rs.{declared_revenue:,.0f} "
                    f"does not match GST turnover slab '{mismatch_data.get('turnover_slab')}'. "
                    f"Declared income is inconsistent with filed returns."
                ),
                "mock": True
            }

        return {
            "result": "CONFIRMED",
            "claim": gstin,
            "registry_data": registry_data,
            "notes": (
                f"GSTIN {gstin} active. "
                f"Declared revenue consistent with GST turnover slab."
            ),
            "mock": True
        }

    # No revenue to cross-check — just confirm format + active status
    fixture = _load_fixture("gst_valid_match.json")
    return {
        "result": "CONFIRMED",
        "claim": gstin,
        "registry_data": fixture.get("data", {}),
        "notes": f"GSTIN {gstin} is active and registered.",
        "mock": True
    }


def _is_valid_gstin_format(gstin: str) -> bool:
    """
    Validate GSTIN format:
    2 digits state code + 10 char PAN + 1 digit entity + Z + 1 checksum
    Example: 27AABCH1234F1Z5
    """
    pattern = r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    return bool(re.match(pattern, gstin.upper()))


def _check_revenue_in_slab(revenue: float, slab: str) -> bool:
    """
    Check if declared revenue falls within the GST turnover slab.
    Allows 20% margin for rounding differences.
    """
    slab_range = TURNOVER_SLABS.get(slab)
    if not slab_range:
        return True  # unknown slab, don't flag

    low, high = slab_range
    margin    = 0.20  # 20% tolerance

    adjusted_low  = low  * (1 - margin)
    adjusted_high = high * (1 + margin)

    return adjusted_low <= revenue <= adjusted_high


def _load_fixture(filename: str) -> dict:
    path = MOCK_DIR / filename
    with open(path, "r") as f:
        return json.load(f)
