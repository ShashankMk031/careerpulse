# Pinned parent Python runtime
FROM python:3.12.8-slim AS builder

WORKDIR /app

# Install compilation tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies using pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn psycopg2-binary python-dotenv boto3 pyarrow

# Production execution stage
FROM python:3.12.8-slim AS runner

# Standard OCI Metadata Labels
LABEL org.opencontainers.image.title="CareerPulse Backend" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.description="Cloud Native Job Market Intelligence API Serving Layer" \
      org.opencontainers.image.source="https://github.com/ShashankMk031/careerpulse"

# Run with python print buffer optimizations
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    APP_ENV=production \
    PYTHONPATH=/app

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy pip wheels from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code under backend package folder
COPY app/ /app/backend/app/
COPY database/ /app/backend/database/

# Run under dedicated non-root application user for system isolation
RUN useradd -u 1001 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Docker healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
