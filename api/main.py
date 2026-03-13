"""
FastAPI backend entry point.
Run locally: uvicorn api.main:app --reload
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routers import papers, experiments, upload

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Agriculture Research DB", version="1.0")

# CORS: localhost in dev; Render URL in prod (same-origin when served from this app)
origins = ["http://localhost:3001"]
if url := os.getenv("RENDER_EXTERNAL_URL"):
    origins.append(url.rstrip("/"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(papers.router, prefix="/api/papers", tags=["papers"])
app.include_router(experiments.router, prefix="/api/experiments", tags=["experiments"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])


# Serve React build in production
static_dir = Path(__file__).parent.parent / "frontend" / "build"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


@app.get("/api")
def api_root():
    return {"status": "ok"}