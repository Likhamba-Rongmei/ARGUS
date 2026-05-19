import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const NODE_COLORS = {
  document:       "#7f77dd",
  claim:          "#1d9e75",
  forensic:       "#ff6b35",
  reconciliation: "#f5c842",
  verdict:        "#ff2d55",
};

const EDGE_COLORS = {
  supports:     "#1d9e75",
  contradicts:  "#ff2d55",
  derived_from: "rgba(255,255,255,0.15)",
  contains:     "rgba(255,255,255,0.1)",
};

export default function EvidenceGraph({ graphData }) {
  const svgRef = useRef();

  useEffect(() => {
    if (!graphData || !graphData.nodes || !graphData.links) return;

    const W = svgRef.current.clientWidth || 700;
    const H = 420;

    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current)
      .attr("width", "100%")
      .attr("height", H);

    // Arrow markers
    const defs = svg.append("defs");
    Object.entries(EDGE_COLORS).forEach(([rel, color]) => {
      defs.append("marker")
        .attr("id", `arrow-${rel}`)
        .attr("viewBox", "0 0 10 10")
        .attr("refX", 18)
        .attr("refY", 5)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto-start-reverse")
        .append("path")
        .attr("d", "M2 1L8 5L2 9")
        .attr("fill", "none")
        .attr("stroke", color)
        .attr("stroke-width", 1.5)
        .attr("stroke-linecap", "round");
    });

    const nodes = graphData.nodes.map(d => ({ ...d }));
    const links = graphData.links.map(d => ({ ...d }));

    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(110))
      .force("charge", d3.forceManyBody().strength(-320))
      .force("center", d3.forceCenter(W / 2, H / 2))
      .force("collision", d3.forceCollide(36));

    // Edges
    const link = svg.append("g").selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", d => EDGE_COLORS[d.relation] || "rgba(255,255,255,0.1)")
      .attr("stroke-width", d => d.relation === "contradicts" ? 2 : 1)
      .attr("stroke-dasharray", d => d.relation === "derived_from" ? "4 3" : null)
      .attr("marker-end", d => `url(#arrow-${d.relation})`);

    // Node groups
    const node = svg.append("g").selectAll("g")
      .data(nodes)
      .join("g")
      .style("cursor", "pointer")
      .call(
        d3.drag()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x; d.fy = d.y;
          })
          .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null; d.fy = null;
          })
      );

    // Node circles
    node.append("circle")
      .attr("r", d => d.node_type === "verdict" ? 22 : d.node_type === "document" ? 18 : 14)
      .attr("fill", d => {
        const base = NODE_COLORS[d.node_type] || "#888";
        return base + "22";
      })
      .attr("stroke", d => NODE_COLORS[d.node_type] || "#888")
      .attr("stroke-width", d => d.node_type === "verdict" ? 2 : 1)
      .style("filter", d => d.node_type === "verdict"
        ? `drop-shadow(0 0 6px ${NODE_COLORS.verdict}88)`
        : "none"
      );

    // Node labels
    node.append("text")
      .text(d => {
        const lines = (d.label || d.id).split("\n");
        return lines[0];
      })
      .attr("text-anchor", "middle")
      .attr("dy", d => d.node_type === "verdict" ? 36 : 28)
      .attr("fill", "rgba(255,255,255,0.6)")
      .attr("font-size", 10)
      .attr("font-family", "'JetBrains Mono', monospace")
      .attr("letter-spacing", "0.04em");

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [graphData]);

  return (
    <div>
      <div style={{
        fontSize: 10,
        letterSpacing: "0.14em",
        color: "rgba(255,255,255,0.3)",
        fontFamily: "'JetBrains Mono', monospace",
        marginBottom: 12,
      }}>
        EVIDENCE GRAPH — DRAG TO EXPLORE
      </div>

      <div style={{
        border: "1px solid rgba(255,255,255,0.06)",
        background: "rgba(0,0,0,0.3)",
        borderRadius: 2,
        overflow: "hidden",
      }}>
        <svg ref={svgRef} style={{ display: "block", width: "100%" }} />
      </div>

      {/* Legend */}
      <div style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "12px 24px",
        marginTop: 12,
      }}>
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <div key={type} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{
              width: 8, height: 8, borderRadius: "50%",
              background: color, display: "inline-block",
            }} />
            <span style={{
              fontSize: 10,
              color: "rgba(255,255,255,0.3)",
              fontFamily: "'JetBrains Mono', monospace",
              letterSpacing: "0.06em",
            }}>{type}</span>
          </div>
        ))}
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 16, height: 1, background: "#ff2d55", display: "inline-block" }} />
          <span style={{
            fontSize: 10,
            color: "rgba(255,255,255,0.3)",
            fontFamily: "'JetBrains Mono', monospace",
            letterSpacing: "0.06em",
          }}>contradicts</span>
        </div>
      </div>
    </div>
  );
}
