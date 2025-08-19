from app.core.config import settings
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import log, set_request_id
from app.db import init_db
from app.api import router as api_router
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time, uuid

REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency", ["path"])

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = str(uuid.uuid4())
        set_request_id(req_id)
        start = time.time()
        try:
            response = await call_next(request)
            status_code = getattr(response, "status_code", 500)
        except Exception as e:
            status_code = 500
            log.error("unhandled_exception", error=str(e))
            raise
        finally:
            dur = time.time() - start
            REQUESTS.labels(request.method, request.url.path, status_code).inc()
            try:
                LATENCY.labels(request.url.path).observe(dur)
            except Exception:
                pass
        return response

app = FastAPI(title="Legal Intel Backend", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestContextMiddleware)

# Routers
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.on_event("startup")
async def on_startup():
    init_db()

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.get("/readyz")
async def readyz():
    # In real prod: test DB connectivity & downstreams
    return {"ready": True}

@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return PlainTextResponse(data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)

# --- DEBUG: list all registered routes (remove later) ---
@app.get("/__debug/routes")
def __debug_routes():
    return [getattr(r, "path", str(r)) for r in app.router.routes]


@app.exception_handler(Exception)
async def app_exception_handler(request: Request, exc: Exception):
    log.error("error", error=str(exc))
    return JSONResponse(status_code=500, content={
        "error": "Something went wrong. Our team has been notified.",
        "request_id": str(uuid.uuid4())[:8]
    })

