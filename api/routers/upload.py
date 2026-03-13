"""
PDF upload with async queue processing.
- Accept multiple files at once
- Queue + limited concurrency (2 at a time to avoid Gemini rate limits)
"""

import importlib.util
import json
import logging
import queue
import sys
import threading
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Queue of (pdf_path, filename) to process
_task_queue: queue.Queue = queue.Queue()
# Semaphore: max 2 concurrent pipeline runs
_max_concurrent = 2
_semaphore = threading.Semaphore(_max_concurrent)
# Status tracking
_processing: list[dict] = []  # [{filename, path}]
_completed: list[dict] = []   # [{filename, status: "ok"|"error", error?}]
_last_error: str | None = None
_lock = threading.Lock()


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _run_pipeline(pdf_path: str) -> None:
    root = Path(__file__).parent.parent.parent
    pipeline_dir = root / "pipeline"
    stem = Path(pdf_path).stem

    parse_mod = _load_module("parse_pdf", pipeline_dir / "1_parse_pdf.py")
    parsed = parse_mod.parse_pdf(pdf_path)
    parsed_path = root / "data" / "parsed" / (stem + ".json")
    parsed_path.parent.mkdir(parents=True, exist_ok=True)
    with open(parsed_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)

    extract_mod = _load_module("extract_llm", pipeline_dir / "2_extract_with_llm.py")
    extracted_path = root / "data" / "extracted" / (stem + ".json")
    extracted_path.parent.mkdir(parents=True, exist_ok=True)
    extract_mod.process_paper(str(parsed_path), str(extracted_path))

    norm_mod = _load_module("normalize", pipeline_dir / "3_normalize.py")
    with open(extracted_path, "r", encoding="utf-8") as f:
        extracted = json.load(f)
    normalized = norm_mod.normalize_paper(extracted)
    normalized.pop("_pending_vocab", None)
    normalized_path = root / "data" / "normalized" / (stem + ".json")
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    with open(normalized_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)

    load_mod = _load_module("load_db", pipeline_dir / "4_load_to_db.py")
    load_mod.load_single(normalized)


def _worker_one(pdf_path: str, filename: str) -> None:
    global _last_error
    try:
        logger.info("Pipeline started: %s", filename)
        _run_pipeline(pdf_path)
        logger.info("Pipeline completed: %s", filename)
        with _lock:
            _completed.append({"filename": filename, "status": "ok"})
            _processing[:] = [p for p in _processing if p["path"] != pdf_path]
    except Exception as e:
        _last_error = str(e)
        logger.exception("Pipeline failed: %s", filename)
        with _lock:
            _completed.append({"filename": filename, "status": "error", "error": str(e)})
            _processing[:] = [p for p in _processing if p["path"] != pdf_path]
    finally:
        _semaphore.release()
        _process_next()


def _process_next() -> None:
    """Take next from queue and start worker if semaphore allows."""
    try:
        pdf_path, filename = _task_queue.get_nowait()
    except queue.Empty:
        return
    if not _semaphore.acquire(blocking=False):
        _task_queue.put((pdf_path, filename))
        return
    with _lock:
        _processing.append({"filename": filename, "path": pdf_path})
    threading.Thread(target=_worker_one, args=(pdf_path, filename), daemon=True).start()


@router.get("/status")
def upload_status():
    """Queue length, currently processing, recent completed/failed."""
    with _lock:
        return {
            "queue_length": _task_queue.qsize(),
            "processing": [p["filename"] for p in _processing],
            "processing_count": len(_processing),
            "completed": _completed[-50:],
            "last_error": _last_error,
        }


@router.post("/")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
):
    """
    Upload one or more PDFs. All are queued and processed asynchronously (max 2 concurrent).
    """
    if not files:
        raise HTTPException(400, "Please upload at least one PDF file")

    root = Path(__file__).parent.parent.parent
    pdf_dir = root / "data" / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    saved: list[dict] = []
    for file in files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            continue
        safe_name = Path(file.filename).name
        pdf_path = pdf_dir / safe_name
        content = await file.read()
        with open(pdf_path, "wb") as f:
            f.write(content)
        _task_queue.put((str(pdf_path), safe_name))
        saved.append({"filename": safe_name, "status": "queued"})

    for _ in range(min(len(saved), _max_concurrent)):
        background_tasks.add_task(_process_next)

    if not saved:
        raise HTTPException(400, "No valid PDF files uploaded")

    return {
        "message": f"Queued {len(saved)} file(s)",
        "files": saved,
        "queue_length": _task_queue.qsize(),
    }
