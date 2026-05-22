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
        from forensics.jpeg_ghost   import analyze_jpeg_ghost
        from forensics.noise_analysis import analyze_noise

        # ELA skipped for PDFs — unreliable due to internal image compression layers
        # PDF tampering is caught by pdf_inspector (incremental updates, font inconsistencies)
        ela_result      = run_ela(file_path) if not filename.lower().endswith(".pdf") else {"result": "SKIPPED", "notes": "ELA not applicable for PDF files.", "flags": []}
        metadata_result = check_metadata(file_path)
        pdf_result      = inspect_pdf(file_path) if filename.lower().endswith(".pdf") else {}
        ts_result       = check_timestamps(file_path)
        ghost_result    = analyze_jpeg_ghost(file_path)
        noise_result    = analyze_noise(file_path)

        forensics_result = {
            "ela":           ela_result,
            "metadata":      metadata_result,
            "pdf_inspector": pdf_result,
            "timestamp":     ts_result,
            "jpeg_ghost":    ghost_result,
            "noise_analysis": noise_result,
        }

        # ── Pipeline 2: Extraction + Reconciliation ──────────────────────────
        from extraction.ocr           import extract_text
        from extraction.groq_extractor import extract_claims

        raw_text      = extract_text(file_path)
        # Clean surrogates from Marathi/regional language OCR before sending to Groq
        if isinstance(raw_text, dict) and "text" in raw_text:
            raw_text["text"] = raw_text["text"].encode("utf-8", errors="ignore").decode("utf-8")
        elif isinstance(raw_text, str):
            raw_text = raw_text.encode("utf-8", errors="ignore").decode("utf-8")
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

        # Add NACH and UTR only if relevant fields exist
        from reconciliation.nach import verify_account
        from reconciliation.dilrmp import verify_property
        from reconciliation.utr  import verify_utr

        if claims_result.get("property_id") or claims_result.get("survey_number"):
            reconciliation_result["dilrmp"] = verify_property(
                claims_result.get("property_id"),
                claims_result.get("survey_number"),
                claims_result.get("owner_name"),
            )

        if claims_result.get("account_number"):
            reconciliation_result["nach"] = verify_account(
                claims_result.get("account_number", ""),
                claims_result.get("account_holder"),
                claims_result.get("bank_name"),
                claims_result.get("opening_balance"),
            )

        # UTR disabled — Groq picks up transaction IDs not actual UTRs
        # if claims_result.get("utr"):
        #     reconciliation_result["utr"] = verify_utr(claims_result.get("utr", ""))

        # ── Verdict ──────────────────────────────────────────────────────────
        from verdict.matrix import compute_verdict

        verdict_result = compute_verdict(forensics_result, reconciliation_result)

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
