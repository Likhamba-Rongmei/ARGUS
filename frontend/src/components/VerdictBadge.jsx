import React from "react";

const VERDICT_CONFIG = {
  "CLEARED": {
    color: "#00ff9d",
    bg: "rgba(0,255,157,0.08)",
    border: "rgba(0,255,157,0.3)",
    icon: "✓",
    sub: "Document verified across both pipelines",
  },
  "LIKELY_FALSE_POSITIVE": {
    color: "#f5c842",
    bg: "rgba(245,200,66,0.08)",
    border: "rgba(245,200,66,0.3)",
    icon: "⚠",
    sub: "Forensic artifact detected — reconciliation confirmed",
  },
  "SOPHISTICATED_FORGERY": {
    color: "#ff6b35",
    bg: "rgba(255,107,53,0.08)",
    border: "rgba(255,107,53,0.3)",
    icon: "◈",
    sub: "Forensically clean — factually impossible. Escalate immediately.",
  },
  "CONFIRMED_FRAUD": {
    color: "#ff2d55",
    bg: "rgba(255,45,85,0.08)",
    border: "rgba(255,45,85,0.3)",
    icon: "✕",
    sub: "Forensic anomaly detected. Ground truth contradiction confirmed.",
  },
};

export default function VerdictBadge({ verdict }) {
  const cfg = VERDICT_CONFIG[verdict] || {
    color: "#888",
    bg: "rgba(136,136,136,0.08)",
    border: "rgba(136,136,136,0.3)",
    icon: "?",
    sub: "Unknown verdict state",
  };

  return (
    <div style={{
      border: `1px solid ${cfg.border}`,
      background: cfg.bg,
      borderRadius: 2,
      padding: "24px 32px",
      display: "flex",
      alignItems: "flex-start",
      gap: 20,
    }}>
      <span style={{
        fontSize: 36,
        color: cfg.color,
        lineHeight: 1,
        fontFamily: "monospace",
        marginTop: 2,
      }}>
        {cfg.icon}
      </span>
      <div>
        <div style={{
          fontSize: 22,
          fontWeight: 700,
          color: cfg.color,
          letterSpacing: "0.08em",
          fontFamily: "'JetBrains Mono', monospace",
          marginBottom: 6,
        }}>
          {verdict}
        </div>
        <div style={{
          fontSize: 13,
          color: "rgba(255,255,255,0.5)",
          fontFamily: "'JetBrains Mono', monospace",
          letterSpacing: "0.03em",
        }}>
          {cfg.sub}
        </div>
      </div>
    </div>
  );
}
