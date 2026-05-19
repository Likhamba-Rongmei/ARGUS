"""graph.py — /api/graph/{job_id}"""

from fastapi import APIRouter, HTTPException
from routers.upload import jobs

router = APIRouter()


@router.get("/graph/{job_id}")
def get_graph(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    job = jobs[job_id]
    if job["status"] != "complete":
        raise HTTPException(202, f"Job status: {job['status']}")
    return job["graph"]
