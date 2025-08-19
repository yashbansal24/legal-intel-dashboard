import os
from typing import Iterable, List, Dict  # NEW
from fastapi import UploadFile
from app.core.config import settings
from app.services.text_utils import extract_text_from_file
from app.services.extraction import extract_metadata
from app.core.logging import log

async def ingest_files(files: Iterable[UploadFile]) -> List[Dict[str, object]]:
    log.info("ingest_start")
    results: List[Dict[str, object]] = []
    count = 0
    for f in files:
        count += 1
        try:
            log.info(
                "ingest_file_begin",
                filename=f.filename,
                content_type=getattr(f, "content_type", None),
                declared_size=getattr(f, "size", None),
                max_mb=settings.MAX_UPLOAD_MB,
            )

            if getattr(f, "size", None) and f.size > settings.MAX_UPLOAD_MB * 1024 * 1024:
                log.warn("ingest_file_rejected_size", filename=f.filename, size=f.size)
                raise ValueError(f"{f.filename} exceeds {settings.MAX_UPLOAD_MB}MB limit")

            # Persist file to disk (dev) — in prod, switch to S3 based on STORAGE_BACKEND
            dest = os.path.join(settings.DATA_DIR, f.filename)
            with open(dest, "wb") as out:
                content = await f.read()
                out.write(content)
            log.info("ingest_file_write_done", filename=f.filename, path=dest, bytes=len(content))

            ctype = f.content_type or "application/octet-stream"
            log.debug("ingest_extract_start", filename=f.filename, content_type=ctype)
            text = extract_text_from_file(dest, ctype)
            log.debug("ingest_extract_done", filename=f.filename, text_len=len(text) if text else 0)

            md = extract_metadata(text)
            log.info("ingest_metadata_extracted", filename=f.filename, **{k: v for k, v in md.items() if v})

            record = {
                "filename": f.filename,
                "content_type": f.content_type,
                "size_bytes": len(content),
                "text": text,
                **md,
            }
            results.append(record)
            log.info("ingest_file_appended", filename=f.filename)
        except Exception as e:
            log.error("ingest_file_error", filename=getattr(f, "filename", None), error=str(e))
            raise

    log.info("ingest_end", files_processed=count, results=len(results))
    return results
