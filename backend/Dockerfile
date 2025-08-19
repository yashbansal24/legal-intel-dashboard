FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     poppler-utils     && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . /app

ENV BIND=0.0.0.0:8000
EXPOSE 8000

# Non-root user (security best practice)
RUN useradd -ms /bin/bash appuser
USER appuser

CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]
