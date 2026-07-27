# ────────────────────────────────────────────────────────────────────────────
# Resume Parser System — Production Dockerfile
#
# Multi-stage build:
#   base        — shared OS packages and Python configuration
#   deps        — Python dependencies layer (cached separately)
#   development — deps + live-reload mount for local dev
#   production  — hardened, non-root, minimal final image
#
# Build for production:
#   docker build --target production -t resume-parser-system:latest .
#
# NOTE: sentence-transformers pulls PyTorch (~1.5 GB).
#       The production stage pre-downloads the embedding model so the
#       container is fully self-contained and has no cold-start delay.
# ────────────────────────────────────────────────────────────────────────────

# ── Stage 1: base ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

LABEL org.opencontainers.image.title="Resume Parser System" \
      org.opencontainers.image.description="Production-grade resume parsing and ATS platform" \
      org.opencontainers.image.source="https://github.com/hamsini105/project"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120

WORKDIR /app

# System packages required by PyMuPDF and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgl1-mesa-glx \
        curl \
    && rm -rf /var/lib/apt/lists/*


# ── Stage 2: deps ─────────────────────────────────────────────────────────────
FROM base AS deps

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# ── Stage 3: development ──────────────────────────────────────────────────────
FROM deps AS development

COPY requirements-dev.txt* ./
RUN test -f requirements-dev.txt \
    && pip install --no-cache-dir -r requirements-dev.txt \
    || true

# Copy source — will be overridden by volume mount in docker-compose
COPY . .

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0"]


# ── Stage 4: production ───────────────────────────────────────────────────────
FROM deps AS production

# Create a non-root user — never run production workloads as root
RUN groupadd --gid 1001 appuser \
 && useradd  --uid 1001 --gid appuser \
             --shell /bin/bash \
             --create-home \
             --no-log-init \
             appuser

# Pre-download the embedding model into the image so the container is
# fully self-contained.  This avoids runtime network calls and cold-start
# latency in production environments with restricted egress.
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('all-MiniLM-L6-v2'); \
print('Embedding model cached successfully.')"

# Copy application source (ownership set to appuser)
COPY --chown=appuser:appuser . .

# Remove files that have no place in production
RUN rm -rf \
        tests/ \
        docs/ \
        .github/ \
        .pre-commit-config.yaml \
        requirements-dev.txt \
        *.test.py \
        *_tests.py \
        .env \
        .env.* \
    && find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=true", \
     "--server.maxUploadSize=10"]
