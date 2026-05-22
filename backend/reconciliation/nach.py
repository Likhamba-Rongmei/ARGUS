# backend/reconciliation/nach.py
# RBI Account Aggregator / NACH verification
# Checks: account number, account holder name, opening balance

import json
import os
from pathlib import Path

MOCK_DIR  = Path(__file__).parent.parent.parent / "mock_apis"
MOCK_MODE = os.getenv("NACH_MOCK", "true").lower() == "true"

BALANCE_TOLERANCE = 0.05  # 5% tolerance for balance differences


def verify_account(
    account_number: str,
    account_holder: str = None,
    bank_name: str = None,
    opening_balance: float = None,
) -> dict:
    if not account_number:
        return {
            "result": "UNVERIFIED",
            "claim": None,
            "registry_data": None,
            "notes": "No account number found in document to verify",
        }

    if MOCK_MODE:
        return _mock_verify_account(account_number, account_holder, bank_name, opening_balance)

    raise NotImplementedError("Production AA/NACH API not configured")


def _mock_verify_account(
    account_number: str,
    account_holder: str = None,
    bank_name: str = None,
    opening_balance: float = None,
) -> dict:
    fixture = _load_fixture("nach_account_found.json")
    registry_data = fixture.get("data", {})

    if not registry_data:
        return {
            "result": "CONTRADICTED",
            "claim": account_number,
            "registry_data": None,
            "notes": "Account not found in AA framework.",
            "mock": True,
        }

    discrepancies = []

    # ── Check 1: Account number ──────────────────────────────────────────────
    if account_number.strip() != registry_data.get("account_number", "").strip():
        return {
            "result": "CONTRADICTED",
            "claim": account_number,
            "registry_data": None,
            "notes": f"Account number {account_number} not found in AA framework.",
            "mock": True,
        }

    # ── Check 2: Account holder name ─────────────────────────────────────────
    if account_holder and registry_data.get("account_holder"):
        claimed  = _clean_name(account_holder)
        registry = _clean_name(registry_data["account_holder"])
        if claimed not in registry and registry not in claimed and _word_overlap(claimed, registry) < 0.5:
            discrepancies.append(
                f"Account holder mismatch: claimed='{account_holder}', "
                f"registry='{registry_data['account_holder']}'"
            )

    # ── Check 3: Balance ─────────────────────────────────────────────────────
    if opening_balance is not None and registry_data.get("opening_balance") is not None:
        registry_balance = float(registry_data["opening_balance"])
        claimed_balance  = float(opening_balance)
        if registry_balance != 0:
            diff = abs(claimed_balance - registry_balance) / registry_balance
            if diff > BALANCE_TOLERANCE:
                discrepancies.append(
                    f"Balance mismatch: claimed=₹{claimed_balance:,.2f}, "
                    f"registry=₹{registry_balance:,.2f} "
                    f"(difference: {diff*100:.1f}%)"
                )

    if discrepancies:
        return {
            "result": "CONTRADICTED",
            "claim": account_number,
            "registry_data": registry_data,
            "notes": " | ".join(discrepancies),
            "discrepancies": discrepancies,
            "mock": True,
        }

    matched = {
        "account_number": account_number,
        "account_holder": registry_data.get("account_holder"),
        "bank_name":      registry_data.get("bank_name"),
        "kyc_verified":   registry_data.get("kyc_verified"),
    }
    if opening_balance is not None:
        matched["balance_verified"] = True

    return {
        "result": "CONFIRMED",
        "claim": account_number,
        "registry_data": registry_data,
        "matched_fields": matched,
        "notes": (
            f"Account {account_number} verified via RBI Account Aggregator. "
            f"Holder: {registry_data.get('account_holder')}. "
            f"KYC: {'verified' if registry_data.get('kyc_verified') else 'unverified'}."
            + (f" Balance ₹{opening_balance:,.2f} confirmed." if opening_balance else "")
        ),
        "mock": True,
    }


def _clean_name(name: str) -> str:
    name = name.lower().strip()
    for prefix in ["mr.", "mrs.", "dr.", "ms.", "mr ", "mrs ", "dr "]:
        name = name.replace(prefix, "").strip()
    return name


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
