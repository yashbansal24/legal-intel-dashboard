# Legal Documents Dashboard — Production-Ready Take‑Home

A full‑stack, production‑minded implementation of the **Legal Documents Dashboard** challenge. 
This can handle upto millions of users, with attention to reliability, observability, graceful shutdown.


## High-Level Architecture

```
Frontend (Vite + React + TypeScript)
  ├─ Upload (drag & drop, progress, resilient retries, progressBar from uppy)
  ├─ Interrogation View (question -> dynamic table)
  └─ Dashboard (charts & tables from a single aggregated API)
        ▲              ▲
        │              │
        ▼              ▼
Backend (FastAPI + SQLite FTS5; Prometheus metrics; OpenTelemetry-ready)
  ├─ /api/v1/upload       (bulk multi-file upload -> parse & extract metadata)
  ├─ /api/v1/query        (natural-language-ish query -> structured rows)
  ├─ /api/v1/dashboard    (aggregated insights for charts)
  ├─ /healthz, /readyz    (probes)
  └─ /metrics             (Prometheus)
Storage
  ├─ SQLite (dev) -> **Postgres** (prod)
  ├─ Local files (dev) -> **S3** (prod)
  └─ SQLite FTS5 for text search -> **pgvector / external vector DB** (prod)
```

### Design Choices for Real-World Use

- **FastAPI + Gunicorn/Uvicorn** with pre-fork workers and graceful shutdown; request timeouts and body limits.
- **SQLite FTS5** for fast local full-text search in dev. Migrations and models are portable to **Postgres** with trigram/GIN or **pgvector** (notes in code).
- **Batch/aggregate APIs** to avoid N+1 fetches from the frontend. The dashboard is computed server-side in one call.
- **Backpressure & safety nets**: request size limits, rate-limiting middleware (in-memory for dev; recommend ingress / API gateway rate-limits in prod).
- **Observability**: Prometheus `/metrics`, structured JSON logs, request IDs, health/readiness probes. Hooks provided for OpenTelemetry tracing.
- **Resilience patterns**: bounded retries, exponential backoff and cancellation in the UI (TanStack Query), server timeouts, circuit-breaker style short-circuit on downstream failure (mock example).
- **Background processing**: ingestion uses an internal background task now; can be offloaded to Celery/RQ with Redis via `tasks/` for large volumes.
- **Blue/Green & Canary**: containers are stateless; DB migrations are additive-forward. K8s manifests include rolling updates and HPA example.
- **Security**: CORS allowlist, content-type & size checks, basic rate limiting, dependency pinning, headers that disable sniffing, and robust error handler.
- **Scalability path**: swap SQLite for **Postgres**, move blobs to **S3**, add **Redis** for queues, **vector DB** for semantic search, and real LLM integration.

---

## Run Locally (Dev)

### 1) Docker Compose (recommended)
```bash
docker compose -f deploy/docker-compose.yaml up --build
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:5173

### 2) Manual

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend**

```bash
cd frontend
npm i
npm run dev
```

---

## Production Notes

- Run backend with **Gunicorn**: see `backend/gunicorn_conf.py` and Dockerfile.
- Use **Postgres** (RDS/Aurora) with pgbouncer; see env vars and code comments. Use **S3** for document storage; update `STORAGE_BACKEND`.
- Put **API Gateway / Nginx** in front for TLS termination, request/response limits, gzip/brotli, and **rate limits**.
- Enable **OpenTelemetry** exporters (OTLP) to your APM. Prometheus scrape `/metrics`. Grafana dashboards included.
- **Zero-downtime**: rolling deployments (K8s manifests), readiness gates only after DB connectivity established and migrations applied.

---

## Tests

```bash
cd backend
pytest -q
```

---

## How It Scales

- Ingestion can be **queued** (Redis/Celery) with worker autoscaling. Upload returns a Job ID; progress via polling or server-sent events.
- Replace FTS with **vector search** (e.g., pgvector, Qdrant). Embeddings can be generated asynchronously.
- Swap out mock NLP with real **LLM** via API; add cache (Redis) for hot prompts and enforce **circuit breakers** & **timeouts**.
- Shard large tenants by `tenant_id`, partition tables by time, and introduce **CQRS** for dashboard materializations.
