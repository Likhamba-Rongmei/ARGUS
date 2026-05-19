"""status.py — /api/status/{job_id}  (polling endpoint)"""

from fastapi import APIRouter, HTTPException
from routers.upload import jobs

router = APIRouter()


@router.get("/status/{job_id}")
def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    job = jobs[job_id]
    return {"job_id": job_id, "status": job["status"], "error": job.get("error")}
