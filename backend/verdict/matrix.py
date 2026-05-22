def compute_verdict(forensics_result: dict, reconciliation_result: dict) -> dict:

    # Forensic clean = all checks are CLEAN or SKIPPED
    forensic_clean = all(
        check.get("result", "CLEAN") in ("CLEAN", "SKIPPED")
        for check in forensics_result.values()
        if isinstance(check, dict)
    )

    # Reconciliation confirmed = nothing was CONTRADICTED
    # UNVERIFIED / UNKNOWN = no data to check = does not count as failure
    recon_confirmed = not any(
        api.get("result", "").upper() == "CONTRADICTED"
        for api in reconciliation_result.values()
        if isinstance(api, dict)
    )

    if forensic_clean and recon_confirmed:
        verdict = "CLEARED"
        explanation = "Document passed both forensic and reconciliation checks."
    elif not forensic_clean and recon_confirmed:
        verdict = "LIKELY_FALSE_POSITIVE"
        explanation = "Forensic anomaly detected but ground truth confirmed. Likely scan artifact."
    elif forensic_clean and not recon_confirmed:
        verdict = "SOPHISTICATED_FORGERY"
        explanation = "Forensically clean but factually contradicted. Escalate immediately."
    else:
        verdict = "CONFIRMED_FRAUD"
        explanation = "Forensic anomaly detected. Ground truth contradiction confirmed."

    return {
        "verdict":         verdict,
        "explanation":     explanation,
        "forensic_clean":  forensic_clean,
        "recon_confirmed": recon_confirmed,
    }
