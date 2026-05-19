import React, { useState } from "react";

const CHECK_LABELS = {
  ela:           "Error Level Analysis (ELA)",
  metadata:      "Metadata Forensics",
  pdf_inspector: "PDF Structure Inspection",
  timestamp:     "Temporal Consistency",
};

export default function ForensicsPanel({ forensics }) {
  const [open, setOpen] = useState(null);

  if (!forensics) return null;

  const checks = Object.entries(forensics);
  const totalAnomalies = checks.reduce(
    (acc, [, v]) => acc + (v?.anomalies?.length || 0), 0
  );

  return (
    <div>
      <SectionHeader
        label="PIPELINE 1 — FORENSIC ANALYSIS"
        badge={totalAnomalies === 0 ? "CLEAN" : `${totalAnomalies} ANOMALY`}
        badgeColor={totalAnomalies === 0 ? "#00ff9d" : "#ff6b35"}
      />

      <div style={{ display: "flex", flexDirection: "column", gap: 1, marginTop: 12 }}>
        {checks.map(([key, data]) => {
          const anomalies = data?.anomalies || [];
          const score = data?.score ?? 0;
          const isClean = anomalies.length === 0;
          const isOpen = open === key;

          return (
            <div key={key}>
              <div
                onClick={() => setOpen(isOpen ? null : key)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "12px 16px",
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  cursor: "pointer",
                  userSelect: "none",
                  transition: "background 0.1s",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{
                    width: 8, height: 8, borderRadius: "50%",
                    background: isClean ? "#00ff9d" : "#ff6b35",
                    flexShrink: 0,
                    boxShadow: isClean
                      ? "0 0 6px rgba(0,255,157,0.5)"
                      : "0 0 6px rgba(255,107,53,0.5)",
                  }} />
                  <span style={rowLabel}>{CHECK_LABELS[key] || key}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                  <ScoreBar score={score} clean={isClean} />
                  <span style={{
                    fontSize: 10,
                    fontFamily: "'JetBrains Mono', monospace",
                    letterSpacing: "0.08em",
                    color: isClean ? "#00ff9d" : "#ff6b35",
                    minWidth: 60,
                    textAlign: "right",
                  }}>
                    {isClean ? "CLEAN" : `${anomalies.length} FLAG`}
                  </span>
                  <span style={{ color: "rgba(255,255,255,0.2)", fontSize: 12 }}>
                    {isOpen ? "▲" : "▼"}
                  </span>
                </div>
              </div>

              {isOpen && (
                <div style={{
                  padding: "16px 20px",
                  background: "rgba(0,0,0,0.3)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  borderTop: "none",
                }}>
                  {anomalies.length === 0 ? (
                    <div style={cleanMsg}>No anomalies detected.</div>
                  ) : (
                    anomalies.map((a, i) => (
                      <div key={i} style={anomalyRow}>
                        <span style={{ color: "#ff6b35", marginRight: 8 }}>▸</span>
                        {a}
                      </div>
                    ))
                  )}

                  {data?.details && (
                    <details style={{ marginTop: 12 }}>
                      <summary style={detailSummary}>Raw details</summary>
                      <pre style={preStyle}>
                        {JSON.stringify(data.details, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ScoreBar({ score, clean }) {
  return (
    <div style={{
      width: 80, height: 4, background: "rgba(255,255,255,0.08)",
      borderRadius: 2, overflow: "hidden",
    }}>
      <div style={{
        width: `${Math.round(score * 100)}%`,
        height: "100%",
        background: clean ? "#00ff9d" : "#ff6b35",
        transition: "width 0.4s ease",
      }} />
    </div>
  );
}

function SectionHeader({ label, badge, badgeColor }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
      <span style={{
        fontSize: 10,
        letterSpacing: "0.14em",
        color: "rgba(255,255,255,0.3)",
        fontFamily: "'JetBrains Mono', monospace",
      }}>{label}</span>
      <span style={{
        fontSize: 10,
        letterSpacing: "0.1em",
        color: badgeColor,
        fontFamily: "'JetBrains Mono', monospace",
        border: `1px solid ${badgeColor}33`,
        padding: "2px 8px",
        borderRadius: 2,
      }}>{badge}</span>
    </div>
  );
}

const rowLabel = {
  fontSize: 13,
  color: "rgba(255,255,255,0.7)",
  fontFamily: "'JetBrains Mono', monospace",
  letterSpacing: "0.02em",
};

const anomalyRow = {
  fontSize: 12,
  color: "rgba(255,255,255,0.6)",
  fontFamily: "'JetBrains Mono', monospace",
  padding: "4px 0",
  borderBottom: "1px solid rgba(255,255,255,0.04)",
  letterSpacing: "0.02em",
  lineHeight: 1.6,
};

const cleanMsg = {
  fontSize: 12,
  color: "#00ff9d",
  fontFamily: "'JetBrains Mono', monospace",
  opacity: 0.7,
};

const detailSummary = {
  fontSize: 11,
  color: "rgba(255,255,255,0.3)",
  fontFamily: "'JetBrains Mono', monospace",
  cursor: "pointer",
  letterSpacing: "0.06em",
  marginTop: 8,
};

const preStyle = {
  fontSize: 11,
  color: "rgba(255,255,255,0.4)",
  fontFamily: "'JetBrains Mono', monospace",
  background: "rgba(0,0,0,0.4)",
  padding: 12,
  borderRadius: 2,
  overflow: "auto",
  marginTop: 8,
  maxHeight: 200,
  lineHeight: 1.6,
};
