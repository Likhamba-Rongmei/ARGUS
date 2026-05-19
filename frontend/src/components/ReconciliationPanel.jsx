import React, { useState } from "react";

const API_LABELS = {
  mca21:  "MCA21 — Company Registry",
  gst:    "GST Network — Tax Records",
  dilrmp: "DILRMP — Land Records",
};

const STATUS_CONFIG = {
  confirmed: { color: "#00ff9d", label: "CONFIRMED" },
  contradicted: { color: "#ff2d55", label: "CONTRADICTED" },
  not_found: { color: "#f5c842", label: "NOT FOUND" },
  unknown: { color: "#888", label: "UNKNOWN" },
};

export default function ReconciliationPanel({ reconciliation, claims }) {
  const [open, setOpen] = useState(null);

  if (!reconciliation) return null;

  const checks = Object.entries(reconciliation);
  const allConfirmed = checks.every(([, v]) => v?.status === "confirmed");
  const anyContradicted = checks.some(([, v]) => v?.status === "contradicted");

  const overallColor = anyContradicted ? "#ff2d55" : allConfirmed ? "#00ff9d" : "#f5c842";
  const overallLabel = anyContradicted ? "CONTRADICTED" : allConfirmed ? "CONFIRMED" : "PARTIAL";

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={sectionLabel}>PIPELINE 2 — GROUND TRUTH RECONCILIATION</span>
        <span style={{
          fontSize: 10,
          letterSpacing: "0.1em",
          color: overallColor,
          fontFamily: "'JetBrains Mono', monospace",
          border: `1px solid ${overallColor}33`,
          padding: "2px 8px",
          borderRadius: 2,
        }}>{overallLabel}</span>
      </div>

      {/* Extracted claims summary */}
      {claims && (
        <div style={{
          marginTop: 12,
          marginBottom: 2,
          padding: "10px 14px",
          background: "rgba(255,255,255,0.02)",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: 2,
        }}>
          <div style={{ ...sectionLabel, marginBottom: 8 }}>EXTRACTED CLAIMS</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px 24px" }}>
            {Object.entries(claims).map(([k, v]) =>
              v ? (
                <div key={k} style={{ display: "flex", gap: 8 }}>
                  <span style={claimKey}>{k}</span>
                  <span style={claimVal}>{String(v)}</span>
                </div>
              ) : null
            )}
          </div>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 1, marginTop: 1 }}>
        {checks.map(([key, data]) => {
          const status = data?.status || "unknown";
          const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.unknown;
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
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{
                    width: 8, height: 8, borderRadius: "50%",
                    background: cfg.color,
                    flexShrink: 0,
                    boxShadow: `0 0 6px ${cfg.color}88`,
                  }} />
                  <span style={rowLabel}>{API_LABELS[key] || key.toUpperCase()}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                  <span style={{
                    fontSize: 10,
                    fontFamily: "'JetBrains Mono', monospace",
                    letterSpacing: "0.08em",
                    color: cfg.color,
                  }}>{cfg.label}</span>
                  <span style={{ color: "rgba(255,255,255,0.2)", fontSize: 12 }}>
                    {isOpen ? "▲" : "▼"}
                  </span>
                </div>
              </div>

              {isOpen && (
                <div style={{
                  padding: "14px 20px",
                  background: "rgba(0,0,0,0.3)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  borderTop: "none",
                }}>
                  {data?.detail && (
                    <div style={detailText}>{data.detail}</div>
                  )}
                  {data?.matched_fields && (
                    <div style={{ marginTop: 10 }}>
                      <div style={{ ...sectionLabel, marginBottom: 6 }}>MATCHED FIELDS</div>
                      {Object.entries(data.matched_fields).map(([f, v]) => (
                        <div key={f} style={{ display: "flex", gap: 8, padding: "3px 0" }}>
                          <span style={claimKey}>{f}</span>
                          <span style={{ ...claimVal, color: "#00ff9d" }}>{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {data?.discrepancies && data.discrepancies.length > 0 && (
                    <div style={{ marginTop: 10 }}>
                      <div style={{ ...sectionLabel, marginBottom: 6 }}>DISCREPANCIES</div>
                      {data.discrepancies.map((d, i) => (
                        <div key={i} style={{ ...detailText, color: "#ff2d55" }}>
                          <span style={{ marginRight: 8 }}>▸</span>{d}
                        </div>
                      ))}
                    </div>
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

const sectionLabel = {
  fontSize: 10,
  letterSpacing: "0.14em",
  color: "rgba(255,255,255,0.3)",
  fontFamily: "'JetBrains Mono', monospace",
};

const rowLabel = {
  fontSize: 13,
  color: "rgba(255,255,255,0.7)",
  fontFamily: "'JetBrains Mono', monospace",
  letterSpacing: "0.02em",
};

const claimKey = {
  fontSize: 11,
  color: "rgba(255,255,255,0.3)",
  fontFamily: "'JetBrains Mono', monospace",
  letterSpacing: "0.06em",
  minWidth: 100,
};

const claimVal = {
  fontSize: 11,
  color: "rgba(255,255,255,0.7)",
  fontFamily: "'JetBrains Mono', monospace",
  wordBreak: "break-all",
};

const detailText = {
  fontSize: 12,
  color: "rgba(255,255,255,0.5)",
  fontFamily: "'JetBrains Mono', monospace",
  lineHeight: 1.7,
  letterSpacing: "0.02em",
};
