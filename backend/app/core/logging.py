# backend/app/core/logging.py
import logging, sys, contextvars
import structlog
from typing import Optional   # <-- add this

_request_id_ctx = contextvars.ContextVar("request_id", default=None)

def get_request_id() -> Optional[str]:
    return _request_id_ctx.get()

def set_request_id(val: Optional[str]) -> None:   # <-- just Optional[str]
    _request_id_ctx.set(val)

def configure_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

configure_logging()
log = structlog.get_logger()
