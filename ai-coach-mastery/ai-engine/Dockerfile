# =============================================================================
# ai-engine — Python 3.11 multi-stage build
# Stages: base (deps) -> runtime (uvicorn) / test (pytest)
# WeasyPrint needs pango/cairo system libraries.
# =============================================================================

# ---- Base: system deps + python deps -----------------------------------------
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# WeasyPrint runtime libraries (pango, cairo, gdk-pixbuf, fonts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    shared-mime-info \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---- Test stage: dev deps + source + tests ------------------------------------
FROM base AS test
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY app ./app
COPY tests ./tests
COPY seed_showcase.py .
COPY pyproject.toml .
CMD ["pytest"]

# ---- Runtime stage -------------------------------------------------------------
FROM base AS runtime
RUN groupadd -r app && useradd -r -g app app && \
    mkdir -p /data/artifacts && chown -R app:app /data/artifacts
COPY app ./app
COPY seed_showcase.py .
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
