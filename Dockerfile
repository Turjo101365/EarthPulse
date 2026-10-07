# ==============================================================================
# EarthPulse 3D - Multi-Sensor Geospatial & Telemetry Platform Dockerfile
# ==============================================================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies:
# - libgomp1: OpenMP runtime required by XGBoost and Scikit-learn
# - curl: Required for Docker container healthcheck verification
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Using PyTorch CPU wheel repo to ensure fast, lightweight container builds
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --upgrade pip && \
    pip install --extra-index-url https://download.pytorch.org/whl/cpu -r backend/requirements.txt

# Copy application layers
COPY backend ./backend
COPY frontend ./frontend

# Create non-root application user
RUN useradd --create-home --uid 10001 earthpulse && \
    chown -R earthpulse:earthpulse /app

USER earthpulse

ENV PORT=8050
EXPOSE 8050

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${PORT:-8050}/api/health || exit 1

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8050"]
