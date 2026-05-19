import React, { useState } from "react";
import FileUpload from "../components/FileUpload";
import StatusPoller from "../components/StatusPoller";
import VerdictBadge from "../components/VerdictBadge";
import ForensicsPanel from "../components/ForensicsPanel";
import ReconciliationPanel from "../components/ReconciliationPanel";
import EvidenceGraph from "../components/EvidenceGraph";
import { fetchAllResults } from "../api/argus";

// ── Pipeline stage display ────────────────────────────────────────────────────
const STAGES = [
  { key: "ocr",    label: "OCR EXTRACTION" },
  { key: "llm",    label: "CLAIM EXTRACTION" },
  { key: "ela",    label: "ELA FORENSICS" },
  { key: "meta",   label: "METADATA FORENSICS" },
  { key: "recon",  label: "RECONCILIATION" },
  { key: "graph",  label: "GRAPH BUILD" },
  { key: "verdict",label: "VERDICT MATRIX" },
];

export default function Dashboard() {
  const [phase, setPhase]               = useState("idle");  // idle | uploading | processing | done | error
  const [jobId, setJobId]               = useState(null);
  const [filename, setFilename]         = useState("");
  const [stageIdx, setStageIdx]         = useState(0);
  const [results, setResults]           = useState(null);
  const [errorMsg, setErrorMsg]         = useState("");

  function handleJobStarted(id, name) {
    setJobId(id);
    setFilename(name);
    setPhase("processing");
    setStageIdx(0);
    // Animate through stages while polling (purely cosmetic)
    let i = 0;
    const iv = setInterval(() => {
      i++;
      setStageIdx(i);
      if (i >= STAGES.length - 1) clearInterval(iv);
    }, 900);
  }

  async function handleComplete(id) {
    setStageIdx(STAGES.length);
    try {
      const data = await fetchAllResults(id);
      setResults(data);
      setPhase("done");
    } catch (e) {
      setErrorMsg(e.message);
      setPhase("error");
    }
  }

  function handleError(msg) {
    setErrorMsg(msg);
    setPhase("error");
  }

  function reset() {
    setPhase("idle");
    setJobId(null);
    setFilename("");
    setStageIdx(0);
    setResults(null);
    setErrorMsg("");
  }

  return (
    <div style={pageStyle}>
      {/* ── Header ── */}
      <header style={headerStyle}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
          <span style={logoStyle}>ARGUS</span>
          <span style={sublogoStyle}>
            Adaptive Real-time Graph-based Underwriting Surveillance
          </span>
        </div>
        <div style={headerRight}>
          <Dot color="#00ff9d" pulse />
          <span style={statusText}>SYSTEM ONLINE</span>
        </div>
      </header>

      <div style={mainGrid}>

        {/* ── Left column ── */}
        <div style={leftCol}>

          {/* Upload / processing / reset */}
          {phase === "idle" && (
            <Panel title="SUBMIT DOCUMENT">
              <FileUpload onJobStarted={handleJobStarted} />
            </Panel>
          )}

          {phase === "processing" && (
            <Panel title="ANALYSIS IN PROGRESS">
              <div style={{ marginBottom: 8, fontSize: 11, color: "rgba(255,255,255,0.3)", fontFamily: "mono" }}>
                {filename}
              </div>
              <PipelineProgress stages={STAGES} currentIdx={stageIdx} />
            </Panel>
          )}

          {(phase === "done" || phase === "error") && (
            <Panel title="DOCUMENT">
              <div style={{
                fontSize: 12,
                fontFamily: "'JetBrains Mono', monospace",
                color: "rgba(255,255,255,0.5)",
                marginBottom: 16,
                letterSpacing: "0.04em",
              }}>
                {filename}
              </div>
              <button onClick={reset} style={resetBtn}>
                ← ANALYSE NEW DOCUMENT
              </button>
            </Panel>
          )}

          {phase === "error" && (
            <div style={{
              marginTop: 8,
              padding: "12px 16px",
              background: "rgba(255,45,85,0.08)",
              border: "1px solid rgba(255,45,85,0.3)",
              borderRadius: 2,
              color: "#ff2d55",
              fontSize: 12,
              fontFamily: "'JetBrains Mono', monospace",
            }}>
              PIPELINE ERROR: {errorMsg}
            </div>
          )}

          {/* Verdict */}
          {results?.verdict && (
            <Panel title="VERDICT">
              <VerdictBadge verdict={results.verdict.verdict} />
              {results.verdict.explanation && (
                <div style={{
                  marginTop: 12,
                  fontSize: 12,
                  color: "rgba(255,255,255,0.4)",
                  fontFamily: "'JetBrains Mono', monospace",
                  lineHeight: 1.7,
                  letterSpacing: "0.02em",
                }}>
                  {results.verdict.explanation}
                </div>
              )}
            </Panel>
          )}

          {/* Forensics */}
          {results?.forensics && (
            <Panel>
              <ForensicsPanel forensics={results.forensics} />
            </Panel>
          )}

          {/* Reconciliation */}
          {results?.reconciliation && (
            <Panel>
              <ReconciliationPanel
                reconciliation={results.reconciliation}
                claims={results.claims}
              />
            </Panel>
          )}
        </div>

        {/* ── Right column ── */}
        <div style={rightCol}>
          {results?.graph ? (
            <Panel style={{ height: "100%", minHeight: 500 }}>
              <EvidenceGraph graphData={results.graph} />
            </Panel>
          ) : (
            <div style={graphPlaceholder}>
              <div style={{ fontSize: 11, letterSpacing: "0.1em", color: "rgba(255,255,255,0.15)", fontFamily: "'JetBrains Mono', monospace" }}>
                EVIDENCE GRAPH<br />PENDING ANALYSIS
              </div>
            </div>
          )}

          {/* Four-state matrix legend */}
          <Panel title="VERDICT MATRIX">
            <MatrixTable />
          </Panel>
        </div>

      </div>

      {/* Background polling */}
      {phase === "processing" && jobId && (
        <StatusPoller
          jobId={jobId}
          onComplete={handleComplete}
          onError={handleError}
        />
      )}
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Panel({ title, children, style = {} }) {
  return (
    <div style={{ ...panelStyle, ...style }}>
      {title && (
        <div style={panelTitle}>{title}</div>
      )}
      {children}
    </div>
  );
}

function PipelineProgress({ stages, currentIdx }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {stages.map((s, i) => {
        const done    = i < currentIdx;
        const active  = i === currentIdx;
        const pending = i > currentIdx;
        return (
          <div key={s.key} style={{
            display: "flex", alignItems: "center", gap: 10,
            opacity: pending ? 0.3 : 1,
            transition: "opacity 0.3s",
          }}>
            <span style={{
              width: 7, height: 7, borderRadius: "50%", flexShrink: 0,
              background: done ? "#00ff9d" : active ? "#ff6b35" : "rgba(255,255,255,0.2)",
              boxShadow: active ? "0 0 8px #ff6b3588" : "none",
              animation: active ? "pulse 1s ease-in-out infinite" : "none",
            }} />
            <span style={{
              fontSize: 11,
              fontFamily: "'JetBrains Mono', monospace",
              letterSpacing: "0.08em",
              color: done ? "#00ff9d" : active ? "#ff6b35" : "rgba(255,255,255,0.4)",
            }}>
              {done ? "✓ " : active ? "▶ " : "  "}{s.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function MatrixTable() {
  const rows = [
    { forensic: "Clean",   recon: "Confirmed",    verdict: "CLEARED",              color: "#00ff9d", note: "" },
    { forensic: "Anomaly", recon: "Confirmed",    verdict: "LIKELY FALSE POSITIVE", color: "#f5c842", note: "" },
    { forensic: "Clean",   recon: "Contradicted", verdict: "SOPHISTICATED FORGERY", color: "#ff6b35", note: "← killer feature" },
    { forensic: "Anomaly", recon: "Contradicted", verdict: "CONFIRMED FRAUD",        color: "#ff2d55", note: "" },
  ];

  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr>
          {["FORENSIC", "RECONCILIATION", "VERDICT"].map(h => (
            <th key={h} style={thStyle}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>
            <td style={tdStyle}>{r.forensic}</td>
            <td style={tdStyle}>{r.recon}</td>
            <td style={{ ...tdStyle, color: r.color }}>
              {r.verdict}
              {r.note && <span style={{ color: "rgba(255,255,255,0.3)", marginLeft: 8, fontSize: 10 }}>{r.note}</span>}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Dot({ color, pulse }) {
  return (
    <span style={{
      width: 7, height: 7, borderRadius: "50%",
      background: color, display: "inline-block",
      boxShadow: `0 0 6px ${color}`,
      animation: pulse ? "pulse 2s ease-in-out infinite" : "none",
    }} />
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const pageStyle = {
  minHeight: "100vh",
  background: "#0d0e11",
  color: "#fff",
  padding: "0 0 60px",
};

const headerStyle = {
  borderBottom: "1px solid rgba(255,255,255,0.07)",
  padding: "18px 32px",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  position: "sticky",
  top: 0,
  background: "#0d0e11",
  zIndex: 10,
};

const logoStyle = {
  fontSize: 22,
  fontWeight: 800,
  letterSpacing: "0.18em",
  fontFamily: "'JetBrains Mono', monospace",
  color: "#fff",
};

const sublogoStyle = {
  fontSize: 11,
  letterSpacing: "0.06em",
  color: "rgba(255,255,255,0.25)",
  fontFamily: "'JetBrains Mono', monospace",
};

const headerRight = {
  display: "flex",
  alignItems: "center",
  gap: 8,
};

const statusText = {
  fontSize: 10,
  letterSpacing: "0.12em",
  color: "rgba(255,255,255,0.3)",
  fontFamily: "'JetBrains Mono', monospace",
};

const mainGrid = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: 2,
  padding: "2px",
  maxWidth: 1440,
  margin: "0 auto",
};

const leftCol = {
  display: "flex",
  flexDirection: "column",
  gap: 2,
};

const rightCol = {
  display: "flex",
  flexDirection: "column",
  gap: 2,
};

const panelStyle = {
  background: "rgba(255,255,255,0.02)",
  border: "1px solid rgba(255,255,255,0.06)",
  padding: "20px 24px",
};

const panelTitle = {
  fontSize: 10,
  letterSpacing: "0.14em",
  color: "rgba(255,255,255,0.25)",
  fontFamily: "'JetBrains Mono', monospace",
  marginBottom: 16,
  paddingBottom: 10,
  borderBottom: "1px solid rgba(255,255,255,0.05)",
};

const graphPlaceholder = {
  border: "1px solid rgba(255,255,255,0.06)",
  background: "rgba(0,0,0,0.2)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  minHeight: 420,
  textAlign: "center",
  lineHeight: 2,
};

const resetBtn = {
  fontSize: 11,
  letterSpacing: "0.1em",
  fontFamily: "'JetBrains Mono', monospace",
  color: "rgba(255,255,255,0.4)",
  background: "transparent",
  border: "1px solid rgba(255,255,255,0.12)",
  padding: "8px 16px",
  cursor: "pointer",
  borderRadius: 2,
};

const thStyle = {
  fontSize: 9,
  letterSpacing: "0.12em",
  color: "rgba(255,255,255,0.25)",
  fontFamily: "'JetBrains Mono', monospace",
  textAlign: "left",
  padding: "6px 8px",
  borderBottom: "1px solid rgba(255,255,255,0.06)",
  fontWeight: 400,
};

const tdStyle = {
  fontSize: 11,
  fontFamily: "'JetBrains Mono', monospace",
  color: "rgba(255,255,255,0.55)",
  padding: "8px 8px",
  borderBottom: "1px solid rgba(255,255,255,0.04)",
  letterSpacing: "0.03em",
};
