# ── Stage 1: Install dependencies ────────────────────────────
FROM python:3.12.4-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Production image ────────────────────────────────
FROM python:3.12.4-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code (respects .dockerignore)
COPY . .

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/sh appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

CMD ["python3", "main.py"]