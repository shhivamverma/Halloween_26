# Multi-stage production Dockerfile for Offline Ofrenda Keeper
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    HF_HUB_OFFLINE=1 \
    OLLAMA_HOST=http://host.docker.internal:11434 \
    WHISPER_MODEL=base

# Install system audio dependencies (ffmpeg for faster-whisper decoding)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download and cache faster-whisper model so container starts 100% offline
RUN python3 -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

# Copy application source code
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create persistent data volume directory
RUN mkdir -p /app/data

EXPOSE 8000

# Launch server dynamically binding to Render's assigned $PORT (defaults to 8000)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
