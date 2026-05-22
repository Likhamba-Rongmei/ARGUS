"""
reconciliation/dilrmp.py
DILRMP — Digital India Land Records Modernisation Programme
Verifies property_id, survey_number, owner_name against land registry mock.
"""

import json
from pathlib import Path

MOCK_DIR = Path(__file__).parent.parent.parent / "mock_apis"


def verify_property(
    property_id: str = None,
    survey_number: str = None,
    owner_name: str = None,
) -> dict:
    if not property_id and not survey_number:
        return {
            "result": "UNVERIFIED",
            "notes": "No property ID or survey number found in document.",
            "mock": True,
        }
    return _mock_verify_property(property_id, survey_number, owner_name)


def _mock_verify_property(property_id, survey_number, owner_name):
    fixture = _load_fixture("dilrmp_property_found.json")
    registry = fixture.get("data", {})

    # Check property_id or survey_number
    reg_pid = registry.get("property_id", "").strip()
    reg_survey = registry.get("survey_number", "").strip()

    pid_match = property_id and reg_pid and property_id.strip() == reg_pid
    survey_match = survey_number and reg_survey and survey_number.strip() == reg_survey

    if not pid_match and not survey_match:
        return {
            "result": "CONTRADICTED",
            "claim": property_id or survey_number,
            "registry_data": None,
            "notes": f"Property '{property_id or survey_number}' not found in land registry.",
            "mock": True,
        }

    # Check owner name (case-insensitive) — required if registry has one
    if registry.get("owner_name") and not owner_name:
        return {
            "result": "CONTRADICTED",
            "claim": None,
            "registry_data": registry,
            "notes": "Owner name missing from document but required by registry. Possible redaction or tampering.",
            "mock": True,
        }
    if owner_name and registry.get("owner_name"):
        claimed = owner_name.lower().strip()
        registered = registry["owner_name"].lower().strip()
        if claimed not in registered and registered not in claimed:
            return {
                "result": "CONTRADICTED",
                "claim": owner_name,
                "registry_data": registry,
                "notes": f"Owner mismatch: claimed='{owner_name}', registry='{registry['owner_name']}'.",
                "mock": True,
            }

    return {
        "result": "CONFIRMED",
        "claim": property_id or survey_number,
        "registry_data": registry,
        "notes": f"Property verified in DILRMP registry.",
        "mock": True,
    }


def _load_fixture(filename):
    path = MOCK_DIR / filename
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}
