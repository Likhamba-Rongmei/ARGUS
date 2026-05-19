"""
main.py — FastAPI entry point for ARGUS backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from routers import upload, verdict, claims, forensics, reconciliation, graph, status

app = FastAPI(
    title="ARGUS",
    description="Adaptive Real-time Graph-based Underwriting Surveillance System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router,         prefix="/api")
app.include_router(verdict.router,        prefix="/api")
app.include_router(claims.router,         prefix="/api")
app.include_router(forensics.router,      prefix="/api")
app.include_router(reconciliation.router, prefix="/api")
app.include_router(graph.router,          prefix="/api")
app.include_router(status.router,         prefix="/api")


@app.get("/")
def root():
    return {"system": "ARGUS", "status": "online"}
