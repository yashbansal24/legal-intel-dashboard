from typing import List, Optional
import re

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlmodel import select, Session

from ..db import get_session
from ..models.document import Document
from ..utils.nlp_simple import extract_filters
from app.core.logging import log

router = APIRouter()


class QueryIn(BaseModel):
    question: str


class DocHit(BaseModel):
    document: str
    governing_law: Optional[str] = None


@router.get("/query/ping")
def ping():
    log.debug("query_ping")
    return {"ok": True}


def _find_docs(question: str, session: Session, limit: int) -> List[DocHit]:
    """
    Loose matching:
      - If NLP extracted governing_law/geography -> use case-insensitive CONTAINS (not exact).
      - Otherwise tokenize the question and search across filename + key meta fields.
    """
    qnorm = question.strip().lower()
    filters = extract_filters(question)
    log.info("query_request", question=question, limit=limit, **({k: v for k, v in filters.items()}))

    # 1) If NLP found a place, try partial/case-insensitive DB filtering first
    clauses = []
    if "governing_law" in filters:
        val = filters["governing_law"]
        clauses.append((Document.governing_law != None))  # noqa: E711
        clauses.append(func.lower(Document.governing_law).like(f"%{val.lower()}%"))
    if "geography" in filters:
        val = filters["geography"]
        clauses.append((Document.geography != None))  # noqa: E711
        clauses.append(func.lower(Document.geography).like(f"%{val.lower()}%"))

    if clauses:
        # Build an OR over the field-specific LIKEs
        like_clauses = []
        if len(clauses) >= 2:
            like_clauses = clauses[1::2]
        stmt = select(Document).where(or_(*like_clauses)).limit(limit)
        docs = list(session.exec(stmt))
        log.debug("query_db_like", path="filters", matches=len(docs))
        if docs:
            return [DocHit(document=d.filename, governing_law=d.governing_law) for d in docs]

    # 2) Fallback: keyword search across multiple columns (filename + meta)
    tokens = [t for t in re.findall(r"[a-zA-Z]+", qnorm) if len(t) > 2]
    stop = {"the","and","for","are","with","under","which","show","docs","doc","law","valid","in","by","of"}
    tokens = [t for t in tokens if t not in stop]
    if tokens:
        ors = []
        for t in tokens:
            pat = f"%{t}%"
            ors.extend([
                func.lower(Document.filename).like(pat),
                func.lower(Document.governing_law).like(pat),
                func.lower(Document.geography).like(pat),
                func.lower(Document.agreement_type).like(pat),
                func.lower(Document.industry).like(pat),
            ])
        stmt = select(Document).where(or_(*ors)).limit(limit)
        docs = list(session.exec(stmt))
        log.debug("query_db_like", path="keywords", tokens=tokens, matches=len(docs))
        return [DocHit(document=d.filename, governing_law=d.governing_law) for d in docs]

    # 3) Nothing useful in the question -> return empty
    log.debug("query_no_tokens")
    return []


@router.post("/query/documents", response_model=List[DocHit])
def query_documents_post(
    q: QueryIn,
    session: Session = Depends(get_session),
    limit: int = Query(50, ge=1, le=200),
) -> List[DocHit]:
    docs = _find_docs(q.question, session, limit)
    log.info("query_response", count=len(docs))
    return docs


@router.get("/query/documents", response_model=List[DocHit])
def query_documents_get(
    question: str = Query(..., description="Natural language question"),
    session: Session = Depends(get_session),
    limit: int = Query(50, ge=1, le=200),
) -> List[DocHit]:
    docs = _find_docs(question, session, limit)
    log.info("query_response", count=len(docs))
    return docs
