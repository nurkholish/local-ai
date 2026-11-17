FROM python:3.12-slim AS builder
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip "setuptools>=70.0.0,<81.0.0" wheel

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim

RUN pip install --no-cache-dir --upgrade pip "setuptools>=70.0.0,<81.0.0" wheel

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/app/.local/bin:$PATH \
    PYTHONPATH=/app/src

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/* && \
    useradd -m -u 10001 app

WORKDIR /app

COPY --from=builder /root/.local /home/app/.local
COPY --chown=app:app src /app/src

USER app
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2).status == 200 else 1)" || exit 1

CMD ["uvicorn", "local_ai.interface.http.app:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]