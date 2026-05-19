"""
evidence_graph.py — NetworkX evidence graph builder.

Builds a directed graph where:
  • nodes  = evidence items (document, claims, forensic checks, API results)
  • edges  = supports / contradicts / derived_from relationships

The graph is serialised to a node-link dict that D3.js can consume directly.
"""

import networkx as nx
from typing import Any


# ── Node type constants ──────────────────────────────────────────────────────
NT_DOCUMENT       = "document"
NT_CLAIM          = "claim"
NT_FORENSIC       = "forensic"
NT_RECONCILIATION = "reconciliation"
NT_VERDICT        = "verdict"

# ── Edge relation constants ──────────────────────────────────────────────────
REL_SUPPORTS     = "supports"
REL_CONTRADICTS  = "contradicts"
REL_DERIVED_FROM = "derived_from"
REL_CONTAINS     = "contains"


def build_evidence_graph(
    document_id: str,
    extracted_claims: dict,
    forensics_result: dict,
    reconciliation_result: dict,
    verdict: dict,
) -> dict:
    """
    Assemble all pipeline outputs into a single evidence graph.

    Parameters
    ----------
    document_id           : unique identifier for the uploaded document
    extracted_claims      : output of groq_extractor (company_name, cin, etc.)
    forensics_result      : merged output of ela + metadata + pdf_inspector + timestamp
    reconciliation_result : merged output of mca21 + gst (+ dilrmp if present)
    verdict               : output of matrix.py

    Returns
    -------
    networkx node-link dict, ready for JSON serialisation and D3.js rendering.
    """

    G = nx.DiGraph()

    # ── Root: document node ──────────────────────────────────────────────────
    G.add_node(
        document_id,
        label=f"Document\n{document_id[:12]}…",
        node_type=NT_DOCUMENT,
        color="#7F77DD",   # purple — the source of truth anchor
    )

    # ── Claims extracted by Groq ─────────────────────────────────────────────
    claims_to_check = {
        "company_name": extracted_claims.get("company_name"),
        "cin":          extracted_claims.get("cin"),
        "gstin":        extracted_claims.get("gstin"),
        "turnover":     extracted_claims.get("turnover"),
        "pan":          extracted_claims.get("pan"),
    }

    for field, value in claims_to_check.items():
        if value is None:
            continue
        node_id = f"claim_{field}"
        G.add_node(
            node_id,
            label=f"{field}\n{str(value)[:20]}",
            node_type=NT_CLAIM,
            value=str(value),
            color="#1D9E75",   # teal — claimed facts
        )
        G.add_edge(document_id, node_id, relation=REL_CONTAINS)

    # ── Forensic check nodes ─────────────────────────────────────────────────
    forensic_checks = {
        "ela":          forensics_result.get("ela", {}),
        "metadata":     forensics_result.get("metadata", {}),
        "pdf_inspector":forensics_result.get("pdf_inspector", {}),
        "timestamp":    forensics_result.get("timestamp", {}),
    }

    for check_name, check_data in forensic_checks.items():
        anomalies = check_data.get("anomalies", [])
        score     = check_data.get("score", 0.0)
        is_clean  = len(anomalies) == 0

        node_id = f"forensic_{check_name}"
        G.add_node(
            node_id,
            label=f"{check_name}\n{'clean' if is_clean else f'{len(anomalies)} anomaly'}",
            node_type=NT_FORENSIC,
            anomalies=anomalies,
            score=score,
            color="#1D9E75" if is_clean else "#D85A30",  # teal=clean, coral=anomaly
        )
        G.add_edge(document_id, node_id, relation=REL_DERIVED_FROM)

    # ── Reconciliation nodes ─────────────────────────────────────────────────
    recon_checks = {
        "mca21": reconciliation_result.get("mca21", {}),
        "gst":   reconciliation_result.get("gst", {}),
    }
    if "dilrmp" in reconciliation_result:
        recon_checks["dilrmp"] = reconciliation_result["dilrmp"]

    for api_name, api_data in recon_checks.items():
        status = api_data.get("status", "unknown")   # confirmed / contradicted / not_found
        detail = api_data.get("detail", "")

        is_confirmed = status == "confirmed"
        node_id = f"recon_{api_name}"
        G.add_node(
            node_id,
            label=f"{api_name.upper()}\n{status}",
            node_type=NT_RECONCILIATION,
            status=status,
            detail=detail,
            color="#1D9E75" if is_confirmed else "#D85A30",
        )

        # Link the reconciliation node to the relevant claim
        if api_name == "mca21":
            claim_node = "claim_cin"
        elif api_name == "gst":
            claim_node = "claim_gstin"
        elif api_name == "dilrmp":
            claim_node = "claim_property_id"
        else:
            claim_node = None

        if claim_node and G.has_node(claim_node):
            rel = REL_SUPPORTS if is_confirmed else REL_CONTRADICTS
            G.add_edge(node_id, claim_node, relation=rel)

        G.add_edge(document_id, node_id, relation=REL_DERIVED_FROM)

    # ── Verdict node ─────────────────────────────────────────────────────────
    verdict_label = verdict.get("verdict", "UNKNOWN")
    verdict_colors = {
        "CLEARED":              "#1D9E75",
        "LIKELY FALSE POSITIVE":"#BA7517",
        "SOPHISTICATED FORGERY":"#D85A30",
        "CONFIRMED FRAUD":      "#A32D2D",
    }

    G.add_node(
        "verdict",
        label=f"VERDICT\n{verdict_label}",
        node_type=NT_VERDICT,
        verdict=verdict_label,
        explanation=verdict.get("explanation", ""),
        color=verdict_colors.get(verdict_label, "#888780"),
    )

    # Verdict derives from all forensic and reconciliation nodes
    for node_id in list(G.nodes):
        ntype = G.nodes[node_id].get("node_type")
        if ntype in (NT_FORENSIC, NT_RECONCILIATION):
            G.add_edge(node_id, "verdict", relation=REL_DERIVED_FROM)

    # ── Serialise to node-link dict ──────────────────────────────────────────
    data = nx.node_link_data(G)

    # Flatten node attributes so D3 can read them without drilling into dicts
    for node in data["nodes"]:
        node.setdefault("node_type", "unknown")
        node.setdefault("color", "#888780")

    return data


def graph_summary(graph_data: dict) -> dict:
    """
    Quick stats for logging / status endpoint.
    """
    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", [])

    type_counts: dict[str, int] = {}
    for n in nodes:
        t = n.get("node_type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    contradiction_count = sum(
        1 for l in links if l.get("relation") == REL_CONTRADICTS
    )

    return {
        "total_nodes":      len(nodes),
        "total_edges":      len(links),
        "node_types":       type_counts,
        "contradictions":   contradiction_count,
    }
