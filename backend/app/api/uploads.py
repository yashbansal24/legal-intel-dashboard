from typing import List, Dict, Any
from uuid import uuid4
from pathlib import Path
import os

from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException
from app.core.logging import log

from ..db import get_session
from ..models.document import Document
from ..services.text_utils import extract_text_from_file
from ..services.extraction import extract_metadata

router = APIRouter()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))


def _process_saved_files(saved: List[Dict[str, Any]]) -> None:
    """Runs in background: extract text, derive metadata, store in DB (sync)."""
    log.info("upload_bg_start", files=len(saved))
    session = get_session()
    try:
        for s in saved:
            log.debug("upload_bg_process_file", filename=s.get("original_name"), path=str(s.get("path")))
            text = extract_text_from_file(str(s["path"]), s["content_type"] or "application/octet-stream")
            md = extract_metadata(text)  # agreement_type / governing_law / geography / industry

            doc = Document(
                filename=s["original_name"],
                content_type=s["content_type"],
                size_bytes=s["size_bytes"],
                text=text,
                agreement_type=md.get("agreement_type"),
                governing_law=md.get("governing_law"),
                geography=md.get("geography"),
                industry=md.get("industry"),
            )
            session.add(doc)
        session.commit()
        log.info("upload_bg_committed", files=len(saved))
    finally:
        session.close()
        log.info("upload_bg_end")


@router.post("/upload")
async def upload(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    log.info("upload_request", files=len(files) if files else 0)
    if not files:
        log.warn("upload_no_files")
        raise HTTPException(status_code=400, detail="No files provided.")

    saved: List[Dict[str, Any]] = []
    for f in files:
        log.debug("upload_file_begin", filename=getattr(f, "filename", None), content_type=getattr(f, "content_type", None))
        content = await f.read()
        size = len(content)
        if size > MAX_UPLOAD_MB * 1024 * 1024:
            log.warn("upload_file_too_large", filename=f.filename, size=size, max_mb=MAX_UPLOAD_MB)
            raise HTTPException(status_code=413, detail=f"{f.filename} exceeds {MAX_UPLOAD_MB}MB limit")

        ext = Path(f.filename).suffix or ""
        dest = UPLOAD_DIR / f"{uuid4().hex}{ext}"
        with open(dest, "wb") as out:
            out.write(content)
        log.debug("upload_file_saved", filename=f.filename, path=str(dest), bytes=size)

        saved.append({
            "path": dest,
            "original_name": f.filename,
            "content_type": f.content_type or "application/octet-stream",
            "size_bytes": size,
        })

    background_tasks.add_task(_process_saved_files, saved)
    log.info("upload_accepted", count=len(saved))
    return {"status": "accepted", "count": len(saved), "message": "Files accepted for background processing."}
