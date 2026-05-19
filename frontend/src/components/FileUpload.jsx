import React, { useState, useRef } from "react";
import { uploadDocument } from "../api/argus";

export default function FileUpload({ onJobStarted }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef();

  const ACCEPTED = [".pdf", ".png", ".jpg", ".jpeg", ".tiff"];

  async function handleFile(file) {
    if (!file) return;
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!ACCEPTED.includes(ext)) {
      setError(`Unsupported format: ${ext}. Accepted: ${ACCEPTED.join(", ")}`);
      return;
    }
    setError(null);
    setUploading(true);
    try {
      const { job_id } = await uploadDocument(file);
      onJobStarted(job_id, file.name);
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  }

  return (
    <div>
      <div
        onClick={() => !uploading && inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        style={{
          border: `1px dashed ${dragging ? "#ff6b35" : "rgba(255,255,255,0.15)"}`,
          borderRadius: 2,
          padding: "56px 40px",
          textAlign: "center",
          cursor: uploading ? "wait" : "pointer",
          background: dragging ? "rgba(255,107,53,0.04)" : "transparent",
          transition: "all 0.15s ease",
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED.join(",")}
          style={{ display: "none" }}
          onChange={(e) => handleFile(e.target.files[0])}
        />

        {uploading ? (
          <div>
            <Spinner />
            <div style={labelStyle}>UPLOADING & QUEUING ANALYSIS…</div>
          </div>
        ) : (
          <div>
            <div style={{ fontSize: 32, marginBottom: 16, opacity: 0.3 }}>⬆</div>
            <div style={labelStyle}>
              DROP DOCUMENT HERE OR CLICK TO SELECT
            </div>
            <div style={subStyle}>
              PDF · PNG · JPG · TIFF
            </div>
          </div>
        )}
      </div>

      {error && (
        <div style={{
          marginTop: 12,
          padding: "10px 16px",
          background: "rgba(255,45,85,0.08)",
          border: "1px solid rgba(255,45,85,0.3)",
          borderRadius: 2,
          color: "#ff2d55",
          fontSize: 12,
          fontFamily: "'JetBrains Mono', monospace",
          letterSpacing: "0.03em",
        }}>
          ERROR: {error}
        </div>
      )}
    </div>
  );
}

function Spinner() {
  return (
    <div style={{
      width: 24,
      height: 24,
      border: "2px solid rgba(255,107,53,0.2)",
      borderTop: "2px solid #ff6b35",
      borderRadius: "50%",
      margin: "0 auto 16px",
      animation: "spin 0.8s linear infinite",
    }} />
  );
}

const labelStyle = {
  fontSize: 11,
  letterSpacing: "0.12em",
  color: "rgba(255,255,255,0.4)",
  fontFamily: "'JetBrains Mono', monospace",
  marginBottom: 8,
};

const subStyle = {
  fontSize: 11,
  letterSpacing: "0.08em",
  color: "rgba(255,255,255,0.2)",
  fontFamily: "'JetBrains Mono', monospace",
};
