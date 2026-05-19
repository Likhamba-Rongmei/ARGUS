"""
upload.py — /api/upload

Accepts a document, kicks off the full dual-pipeline analysis,
stores results in the in-memory job store, returns a job_id.
"""

import uuid
import os
import shutil
import asyncio
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel

# ── Shared in-memory job store (imported by all other routers) ───────────────
jobs: dict = {}   # job_id → { status, result, error }

UPLOAD_DIR = Path("/tmp/argus_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()


class JobResponse(BaseModel):
    job_id: str
    status: str


def _run_pipeline(job_id: str, file_path: str, filename: str):
    """Full dual-pipeline analysis — runs in a background thread."""
    try:
        jobs[job_id]["status"] = "running"

        # ── Pipeline 1: Forensics ────────────────────────────────────────────
        from forensics.ela          import run_ela
        from forensics.metadata     import analyze_metadata as check_metadata
        from forensics.pdf_inspector import inspect_pdf
        from forensics.timestamp    import check_timestamps

        ela_result      = run_ela(file_path)
        metadata_result = check_metadata(file_path)
        pdf_result      = inspect_pdf(file_path) if filename.lower().endswith(".pdf") else {}
        ts_result       = check_timestamps(file_path)

        forensics_result = {
            "ela":           ela_result,
            "metadata":      metadata_result,
            "pdf_inspector": pdf_result,
            "timestamp":     ts_result,
        }

        # ── Pipeline 2: Extraction + Reconciliation ──────────────────────────
        from extraction.ocr           import extract_text
        from extraction.groq_extractor import extract_claims

        raw_text      = extract_text(file_path)
        claims_result = extract_claims(raw_text)
        if hasattr(claims_result, "model_dump"):
            claims_result = claims_result.model_dump()

        from reconciliation.mca21 import verify_cin as check_mca21
        from reconciliation.gst   import verify_gstin as check_gst

        mca21_result = check_mca21(claims_result.get("cin", ""))
        gst_result   = check_gst(
            claims_result.get("gstin", ""),
            claims_result.get("turnover"),
        )

        reconciliation_result = {
            "mca21": mca21_result,
            "gst":   gst_result,
        }

        # ── Verdict ──────────────────────────────────────────────────────────
        from verdict.matrix import compute_verdict

        verdict_result = compute_verdict(
            forensics_result.get("result", "ERROR"),
            reconciliation_result.get("result", "UNVERIFIED"),
            forensics_result,
            reconciliation_result,
            claims_result,
            job_id
        )

        # ── Evidence graph ───────────────────────────────────────────────────
        from graph.evidence_graph import build_evidence_graph

        graph_data = build_evidence_graph(
            document_id=job_id,
            extracted_claims=claims_result,
            forensics_result=forensics_result,
            reconciliation_result=reconciliation_result,
            verdict=verdict_result,
        )

        jobs[job_id] = {
            "status":          "complete",
            "filename":        filename,
            "claims":          claims_result,
            "forensics":       forensics_result,
            "reconciliation":  reconciliation_result,
            "verdict":         verdict_result,
            "graph":           graph_data,
        }

    except Exception as exc:
        jobs[job_id] = {"status": "error", "error": str(exc)}


@router.post("/upload", response_model=JobResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    allowed = {".pdf", ".png", ".jpg", ".jpeg", ".tiff"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    job_id    = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{job_id}{ext}"

    with open(save_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    jobs[job_id] = {"status": "queued"}
    background_tasks.add_task(_run_pipeline, job_id, str(save_path), file.filename)

    return JobResponse(job_id=job_id, status="queued")
