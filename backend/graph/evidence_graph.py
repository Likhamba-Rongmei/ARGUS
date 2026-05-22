"""
evidence_graph.py — NetworkX evidence graph builder.
"""

import networkx as nx

NT_DOCUMENT       = "document"
NT_CLAIM          = "claim"
NT_FORENSIC       = "forensic"
NT_RECONCILIATION = "reconciliation"
NT_VERDICT        = "verdict"

REL_SUPPORTS     = "supports"
REL_CONTRADICTS  = "contradicts"
REL_DERIVED_FROM = "derived_from"
REL_CONTAINS     = "contains"

# Which claim field each reconciliation API verifies
RECON_CLAIM_MAP = {
    "mca21":  "claim_cin",
    "gst":    "claim_gstin",
    "dilrmp": "claim_property_id",
    "nach":   "claim_account_number",
    "utr":    "claim_utr",
}


def build_evidence_graph(
    document_id: str,
    extracted_claims: dict,
    forensics_result: dict,
    reconciliation_result: dict,
    verdict: dict,
) -> dict:

    G = nx.DiGraph()

    # ── Root: document node ──────────────────────────────────────────────────
    G.add_node(
        document_id,
        label=f"Document\n{document_id[:12]}…",
        node_type=NT_DOCUMENT,
        color="#7F77DD",
    )

    # ── Claims ───────────────────────────────────────────────────────────────
    claim_fields = {
        "company_name":   extracted_claims.get("company_name"),
        "cin":            extracted_claims.get("cin"),
        "gstin":          extracted_claims.get("gstin"),
        "turnover":       extracted_claims.get("declared_revenue"),
        "pan":            extracted_claims.get("pan"),
        "account_number": extracted_claims.get("account_number"),
        "utr":            extracted_claims.get("utr"),
        "property_id":    extracted_claims.get("property_id"),
    }

    for field, value in claim_fields.items():
        if value is None:
            continue
        node_id = f"claim_{field}"
        G.add_node(
            node_id,
            label=f"{field}\n{str(value)[:20]}",
            node_type=NT_CLAIM,
            value=str(value),
            color="#1D9E75",
        )
        G.add_edge(document_id, node_id, relation=REL_CONTAINS)

    # ── Forensic checks ──────────────────────────────────────────────────────
    for check_name, check_data in forensics_result.items():
        if isinstance(check_data, dict) and check_data.get("result") == "SKIPPED":
            continue
        if not isinstance(check_data, dict):
            continue
        anomalies = check_data.get("anomalies", [])
        result    = check_data.get("result", "CLEAN")
        is_clean  = result in ("CLEAN", "SKIPPED") and len(anomalies) == 0
        score     = check_data.get("score", 0.0)

        node_id = f"forensic_{check_name}"
        G.add_node(
            node_id,
            label=f"{check_name}\n{'clean' if is_clean else 'anomaly'}",
            node_type=NT_FORENSIC,
            anomalies=anomalies,
            score=score,
            color="#1D9E75" if is_clean else "#ff6b35",
        )
        G.add_edge(document_id, node_id, relation=REL_DERIVED_FROM)

    # ── Reconciliation ───────────────────────────────────────────────────────
    for api_name, api_data in reconciliation_result.items():
        if not isinstance(api_data, dict):
            continue
        if api_data.get('result', '').upper() in ('UNVERIFIED', 'UNKNOWN'):
            continue

        status = api_data.get("result", "UNVERIFIED").upper()
        is_confirmed  = status == "CONFIRMED"
        is_unverified = status in ("UNVERIFIED", "UNKNOWN")

        color = "#1D9E75" if is_confirmed else ("#888780" if is_unverified else "#ff2d55")

        node_id = f"recon_{api_name}"
        G.add_node(
            node_id,
            label=f"{api_name.upper()}\n{status}",
            node_type=NT_RECONCILIATION,
            status=status,
            detail=api_data.get("notes", ""),
            color=color,
        )

        # Link to relevant claim
        claim_node = RECON_CLAIM_MAP.get(api_name)
        if claim_node and G.has_node(claim_node):
            rel = REL_SUPPORTS if is_confirmed else (REL_CONTRADICTS if not is_unverified else REL_DERIVED_FROM)
            G.add_edge(node_id, claim_node, relation=rel)

        G.add_edge(document_id, node_id, relation=REL_DERIVED_FROM)

    # ── Verdict ──────────────────────────────────────────────────────────────
    verdict_label = verdict.get("verdict", "UNKNOWN")
    verdict_colors = {
        "CLEARED":               "#1D9E75",
        "LIKELY_FALSE_POSITIVE": "#f5c842",
        "SOPHISTICATED_FORGERY": "#ff6b35",
        "CONFIRMED_FRAUD":       "#ff2d55",
    }

    G.add_node(
        "verdict",
        label=f"VERDICT\n{verdict_label}",
        node_type=NT_VERDICT,
        verdict=verdict_label,
        explanation=verdict.get("explanation", ""),
        color=verdict_colors.get(verdict_label, "#888780"),
    )

    for node_id in list(G.nodes):
        ntype = G.nodes[node_id].get("node_type")
        if ntype in (NT_FORENSIC, NT_RECONCILIATION):
            G.add_edge(node_id, "verdict", relation=REL_DERIVED_FROM)

    # ── Serialise ─────────────────────────────────────────────────────────────
    data = nx.node_link_data(G)
    for node in data["nodes"]:
        node.setdefault("node_type", "unknown")
        node.setdefault("color", "#888780")

    return data


def graph_summary(graph_data: dict) -> dict:
    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", [])
    type_counts: dict[str, int] = {}
    for n in nodes:
        t = n.get("node_type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    contradiction_count = sum(1 for l in links if l.get("relation") == REL_CONTRADICTS)
    return {
        "total_nodes":    len(nodes),
        "total_edges":    len(links),
        "node_types":     type_counts,
        "contradictions": contradiction_count,
    }
