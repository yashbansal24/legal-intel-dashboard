from app.core.config import settings
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import log, set_request_id
from app.db import init_db
from app.api import router as api_router
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time, uuid, asyncio
from typing import Optional, Dict, Deque
from collections import deque
from starlette import status

REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency", ["path"])
_ACTIVE_REQUESTS = 0

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = str(uuid.uuid4())
        set_request_id(req_id)
        start = time.time()
        global _ACTIVE_REQUESTS
        _ACTIVE_REQUESTS += 1
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
            _ACTIVE_REQUESTS = max(0, _ACTIVE_REQUESTS - 1)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'")
        if settings.ENV != "dev":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


class SizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > max_bytes:
            return JSONResponse({"detail": "Request too large"}, status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        return await call_next(request)


class ContentTypeCheckMiddleware(BaseHTTPMiddleware):
    ALLOWED = {"application/json", "multipart/form-data", "text/plain"}

    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            ctype = request.headers.get("content-type", "").split(";")[0].strip().lower()
            if not any(ctype.startswith(a) for a in self.ALLOWED):
                return JSONResponse({"detail": "Unsupported Media Type"}, status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    # Simple in-memory sliding-window limiter for dev use.
    def __init__(self, app, window_s: int = 60, max_requests: int = 120):
        super().__init__(app)
        self.window_s = window_s
        self.max_requests = max_requests
        self.buckets: Dict[str, Deque[float]] = {}

    def _get_ip(self, request: Request) -> str:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        now = time.time()
        ip = self._get_ip(request)
        dq = self.buckets.setdefault(ip, deque())
        while dq and now - dq[0] > self.window_s:
            dq.popleft()
        if len(dq) >= self.max_requests:
            return JSONResponse({"detail": "Too Many Requests"}, status_code=status.HTTP_429_TOO_MANY_REQUESTS)
        dq.append(now)
        return await call_next(request)


class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout_s: Optional[int] = None):
        super().__init__(app)
        self.timeout_s = timeout_s or settings.REQUEST_TIMEOUT_S

    async def dispatch(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.timeout_s)
        except asyncio.TimeoutError:
            return JSONResponse({"detail": "Request timeout"}, status_code=status.HTTP_408_REQUEST_TIMEOUT)

app = FastAPI(title="Legal Intel Backend", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Order: context -> rate-limit -> size/content checks -> timeout -> security
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    window_s=settings.RATE_LIMIT_WINDOW_S,
    max_requests=settings.RATE_LIMIT_MAX_REQUESTS,
)
app.add_middleware(SizeLimitMiddleware)
app.add_middleware(ContentTypeCheckMiddleware)
app.add_middleware(TimeoutMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Routers
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.on_event("startup")
async def on_startup():
    init_db()


@app.on_event("shutdown")
async def on_shutdown():
    # Wait for in-flight requests to finish (best-effort)
    deadline = time.time() + settings.SHUTDOWN_GRACE_PERIOD_S
    while _ACTIVE_REQUESTS > 0 and time.time() < deadline:
        await asyncio.sleep(0.1)
    log.info("graceful_shutdown_complete", active_requests=_ACTIVE_REQUESTS)

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

