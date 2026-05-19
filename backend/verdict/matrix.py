# backend/verdict/matrix.py
# Four-state verdict matrix — core decision engine of ARGUS
# Combines forensic pipeline result + reconciliation result
# into a single structured verdict with action and explanation

from datetime import datetime


# ─── VERDICT CONSTANTS ─────────────────────────────────────────────────────────

class Verdict:
    CLEARED                = "CLEARED"
    LIKELY_FALSE_POSITIVE  = "LIKELY_FALSE_POSITIVE"
    SOPHISTICATED_FORGERY  = "SOPHISTICATED_FORGERY"
    CONFIRMED_FRAUD        = "CONFIRMED_FRAUD"


class ForensicResult:
    CLEAN   = "CLEAN"
    ANOMALY = "ANOMALY"
    ERROR   = "ERROR"


class ReconciliationResult:
    CONFIRMED     = "CONFIRMED"
    CONTRADICTED  = "CONTRADICTED"
    UNVERIFIED    = "UNVERIFIED"


class Action:
    APPROVE          = "APPROVE"
    CLEAR_WITH_NOTE  = "CLEAR_WITH_NOTE"
    ESCALATE         = "ESCALATE"
    HARD_BLOCK       = "HARD_BLOCK"


# ─── VERDICT MATRIX ────────────────────────────────────────────────────────────

MATRIX = {
    (ForensicResult.CLEAN,   ReconciliationResult.CONFIRMED):    Verdict.CLEARED,
    (ForensicResult.ANOMALY, ReconciliationResult.CONFIRMED):    Verdict.LIKELY_FALSE_POSITIVE,
    (ForensicResult.CLEAN,   ReconciliationResult.CONTRADICTED): Verdict.SOPHISTICATED_FORGERY,
    (ForensicResult.ANOMALY, ReconciliationResult.CONTRADICTED): Verdict.CONFIRMED_FRAUD,

    # Edge cases — reconciliation returned unverified
    (ForensicResult.CLEAN,   ReconciliationResult.UNVERIFIED):   Verdict.SOPHISTICATED_FORGERY,
    (ForensicResult.ANOMALY, ReconciliationResult.UNVERIFIED):   Verdict.CONFIRMED_FRAUD,

    # Edge cases — forensics errored
    (ForensicResult.ERROR,   ReconciliationResult.CONFIRMED):    Verdict.LIKELY_FALSE_POSITIVE,
    (ForensicResult.ERROR,   ReconciliationResult.CONTRADICTED): Verdict.CONFIRMED_FRAUD,
    (ForensicResult.ERROR,   ReconciliationResult.UNVERIFIED):   Verdict.CONFIRMED_FRAUD,
}

ACTION_MAP = {
    Verdict.CLEARED:               Action.APPROVE,
    Verdict.LIKELY_FALSE_POSITIVE: Action.CLEAR_WITH_NOTE,
    Verdict.SOPHISTICATED_FORGERY: Action.ESCALATE,
    Verdict.CONFIRMED_FRAUD:       Action.HARD_BLOCK,
}

VERDICT_LABELS = {
    Verdict.CLEARED:               "✅ Cleared",
    Verdict.LIKELY_FALSE_POSITIVE: "⚠️  Likely False Positive",
    Verdict.SOPHISTICATED_FORGERY: "🚨 Sophisticated Forgery",
    Verdict.CONFIRMED_FRAUD:       "❌ Confirmed Fraud",
}

VERDICT_DESCRIPTIONS = {
    Verdict.CLEARED: (
        "Document passed both forensic analysis and external reconciliation. "
        "No anomalies detected. High confidence in document authenticity."
    ),
    Verdict.LIKELY_FALSE_POSITIVE: (
        "Forensic anomalies detected but document claims confirmed by external registry. "
        "Anomalies are likely scan artifacts or compression noise. "
        "Auto-cleared — no further review required."
    ),
    Verdict.SOPHISTICATED_FORGERY: (
        "Document passed all forensic checks but claims could not be confirmed "
        "by external registry. Document is forensically clean but factually false. "
        "This is the highest-risk fraud pattern. Escalate immediately."
    ),
    Verdict.CONFIRMED_FRAUD: (
        "Document failed both forensic analysis and external reconciliation. "
        "Forensic anomalies detected and claims contradict registry data. "
        "Hard block applied. Log for investigation."
    ),
}


# ─── CONFIDENCE SCORING ────────────────────────────────────────────────────────

def compute_confidence(
    forensic_result: str,
    reconciliation_result: str,
    forensic_details: dict,
    reconciliation_details: dict
) -> float:
    """
    Compute a confidence score (0.0 - 1.0) for the verdict.
    Higher = more certain about the verdict.
    """
    base = 0.5
    score = base

    # Forensic contribution
    if forensic_result == ForensicResult.CLEAN:
        score += 0.2
    elif forensic_result == ForensicResult.ANOMALY:
        # More flags = higher confidence in anomaly
        flag_count = len(forensic_details.get("all_flags", []))
        score += min(0.2, flag_count * 0.05)
    elif forensic_result == ForensicResult.ERROR:
        score -= 0.1  # less confident if forensics errored

    # Reconciliation contribution
    if reconciliation_result == ReconciliationResult.CONFIRMED:
        score += 0.25
    elif reconciliation_result == ReconciliationResult.CONTRADICTED:
        # More contradictions = higher confidence in fraud
        contradiction_count = len(reconciliation_details.get("contradictions", []))
        score += min(0.25, contradiction_count * 0.1)
    elif reconciliation_result == ReconciliationResult.UNVERIFIED:
        score -= 0.05

    # ELA anomaly score contribution
    ela_score = forensic_details.get("ela_anomaly_score", 0.0)
    if ela_score > 20.0:
        score += 0.05

    return round(min(1.0, max(0.0, score)), 4)


# ─── FORENSIC AGGREGATOR ───────────────────────────────────────────────────────

def aggregate_forensic_result(
    ela: dict,
    metadata: dict,
    pdf_inspector: dict
) -> dict:
    """
    Combine results from all three forensic checks
    into a single forensic pipeline result.

    Any single ANOMALY = overall ANOMALY.
    All must be CLEAN for overall CLEAN.
    """
    all_flags = []
    all_notes = []

    results = {
        "ela":           ela.get("result",      ForensicResult.ERROR),
        "metadata":      metadata.get("result", ForensicResult.ERROR),
        "pdf_inspector": pdf_inspector.get("result", ForensicResult.ERROR)
            if pdf_inspector else ForensicResult.CLEAN  # pdf_inspector only runs on PDFs
    }

    # Collect all flags
    all_flags.extend(ela.get("flags",           []))
    all_flags.extend(metadata.get("flags",      []))
    all_flags.extend(pdf_inspector.get("flags", []) if pdf_inspector else [])

    # Collect all notes
    if ela.get("notes"):
        all_notes.append(f"ELA: {ela['notes']}")
    if metadata.get("notes"):
        all_notes.append(f"Metadata: {metadata['notes']}")
    if pdf_inspector and pdf_inspector.get("notes"):
        all_notes.append(f"PDF Structure: {pdf_inspector['notes']}")

    # Determine overall result
    any_anomaly = any(r == ForensicResult.ANOMALY for r in results.values())
    any_error   = any(r == ForensicResult.ERROR   for r in results.values())

    if any_anomaly:
        overall = ForensicResult.ANOMALY
    elif any_error:
        overall = ForensicResult.ERROR
    else:
        overall = ForensicResult.CLEAN

    return {
        "result":           overall,
        "individual":       results,
        "all_flags":        all_flags,
        "all_notes":        all_notes,
        "ela_anomaly_score": ela.get("anomaly_score", 0.0),
        "heatmap_path":     ela.get("heatmap_path")
    }


# ─── RECONCILIATION AGGREGATOR ─────────────────────────────────────────────────

def aggregate_reconciliation_result(
    mca21: dict,
    gst: dict
) -> dict:
    """
    Combine results from all reconciliation API checks
    into a single reconciliation pipeline result.

    Any CONTRADICTED = overall CONTRADICTED.
    All must be CONFIRMED for overall CONFIRMED.
    If none confirmed and none contradicted = UNVERIFIED.
    """
    results = {}
    contradictions = []
    confirmations  = []

    if mca21:
        results["mca21"] = mca21.get("result", ReconciliationResult.UNVERIFIED)
        if results["mca21"] == ReconciliationResult.CONTRADICTED:
            contradictions.append(f"MCA21: {mca21.get('notes', '')}")
        elif results["mca21"] == ReconciliationResult.CONFIRMED:
            confirmations.append("MCA21 verified")

    if gst:
        results["gst"] = gst.get("result", ReconciliationResult.UNVERIFIED)
        if results["gst"] == ReconciliationResult.CONTRADICTED:
            contradictions.append(f"GST: {gst.get('notes', '')}")
        elif results["gst"] == ReconciliationResult.CONFIRMED:
            confirmations.append("GST verified")

    # Determine overall
    if contradictions:
        overall = ReconciliationResult.CONTRADICTED
    elif confirmations:
        overall = ReconciliationResult.CONFIRMED
    else:
        overall = ReconciliationResult.UNVERIFIED

    return {
        "result":         overall,
        "individual":     results,
        "contradictions": contradictions,
        "confirmations":  confirmations
    }


# ─── MAIN VERDICT ENGINE ───────────────────────────────────────────────────────

def compute_verdict(
    forensic_result:        str,
    reconciliation_result:  str,
    forensic_details:       dict,
    reconciliation_details: dict,
    claims:                 dict,
    document_id:            str
) -> dict:
    """
    Core verdict engine.
    Takes aggregated pipeline results, returns full verdict object.

    Args:
        forensic_result:       "CLEAN" | "ANOMALY" | "ERROR"
        reconciliation_result: "CONFIRMED" | "CONTRADICTED" | "UNVERIFIED"
        forensic_details:      aggregated forensic dict
        reconciliation_details: aggregated reconciliation dict
        claims:                extracted document claims dict
        document_id:           document identifier

    Returns full verdict dict ready for API response and dashboard.
    """

    # Look up verdict from matrix
    verdict = MATRIX.get(
        (forensic_result, reconciliation_result),
        Verdict.CONFIRMED_FRAUD  # default to worst case if combination unknown
    )

    action     = ACTION_MAP[verdict]
    label      = VERDICT_LABELS[verdict]
    description = VERDICT_DESCRIPTIONS[verdict]

    confidence = compute_confidence(
        forensic_result,
        reconciliation_result,
        forensic_details,
        reconciliation_details
    )

    # Build summary sentence for dashboard header
    summary = _build_summary(
        verdict,
        forensic_result,
        reconciliation_result,
        forensic_details,
        reconciliation_details,
        claims
    )

    return {
        "document_id":            document_id,
        "verdict":                verdict,
        "verdict_label":          label,
        "verdict_description":    description,
        "forensic_result":        forensic_result,
        "reconciliation_result":  reconciliation_result,
        "confidence":             confidence,
        "action":                 action,
        "summary":                summary,
        "forensic_details":       forensic_details,
        "reconciliation_details": reconciliation_details,
        "claims":                 claims,
        "processed_at":           datetime.utcnow().isoformat() + "Z"
    }


# ─── FULL PIPELINE RUNNER ──────────────────────────────────────────────────────

def run_verdict_pipeline(
    ela_result:          dict,
    metadata_result:     dict,
    pdf_inspector_result: dict,
    mca21_result:        dict,
    gst_result:          dict,
    claims:              dict,
    document_id:         str
) -> dict:
    """
    Convenience function — takes raw results from all modules,
    aggregates them, and returns the final verdict.

    This is what the FastAPI router calls.
    """
    # Aggregate forensic pipeline
    forensic_agg = aggregate_forensic_result(
        ela_result,
        metadata_result,
        pdf_inspector_result
    )

    # Aggregate reconciliation pipeline
    reconciliation_agg = aggregate_reconciliation_result(
        mca21_result,
        gst_result
    )

    # Compute final verdict
    verdict = compute_verdict(
        forensic_result        = forensic_agg["result"],
        reconciliation_result  = reconciliation_agg["result"],
        forensic_details       = forensic_agg,
        reconciliation_details = reconciliation_agg,
        claims                 = claims,
        document_id            = document_id
    )

    return verdict


# ─── HELPERS ───────────────────────────────────────────────────────────────────

def _build_summary(
    verdict:                str,
    forensic_result:        str,
    reconciliation_result:  str,
    forensic_details:       dict,
    reconciliation_details: dict,
    claims: dict
) -> str:
    lines = []
    lines.append(f"Verdict: {verdict}")
    lines.append(f"Forensic: {forensic_result} | Reconciliation: {reconciliation_result}")
    if forensic_details.get("anomalies"):
        lines.append(f"Forensic anomalies: {', '.join(forensic_details['anomalies'])}")
    if reconciliation_details.get("discrepancies"):
        lines.append(f"Discrepancies: {', '.join(reconciliation_details['discrepancies'])}")
    if claims:
        lines.append(f"Claims extracted: {', '.join(k for k,v in claims.items() if v)}")
    return " | ".join(lines)
