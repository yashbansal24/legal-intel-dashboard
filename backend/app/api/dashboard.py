from fastapi import APIRouter, Depends
from sqlmodel import select, Session

from ..db import get_session
from ..models.document import Document
from app.services.dashboard import build_dashboard
from app.core.logging import log

router = APIRouter()


@router.get("/dashboard")
def dashboard(session: Session = Depends(get_session)):
    log.info("dashboard_request")
    docs = list(session.exec(select(Document)))
    resp = build_dashboard(docs)
    log.info("dashboard_response", documents=len(docs), has_stats=bool(resp))
    return resp
