# Multi-stage production Dockerfile for Offline Ofrenda Keeper
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    OLLAMA_HOST=http://host.docker.internal:11434 \
    WHISPER_MODEL=base \
    HF_HOME=/root/.cache/huggingface \
    TTS_HOME=/app/data/tts_cache \
    COQUI_TOS_AGREED=1

# Install system audio dependencies (ffmpeg for whisper, libsndfile1 for torchaudio/soundfile)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies: explicit CPU PyTorch first to prevent CUDA packages, then full requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Verify that torch, torchaudio, and TTS import cleanly in the container build environment
RUN python3 -c "import torch, torchaudio, TTS; print(f'VERIFIED: Torch {torch.__version__}, Torchaudio {torchaudio.__version__}, TTS {TTS.__version__}')"

# Pre-download and cache faster-whisper model so container can run 100% offline
RUN HF_HUB_OFFLINE=0 python3 -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

# Enforce strictly offline Hugging Face Hub mode for runtime container
ENV HF_HUB_OFFLINE=1

# Copy application source code
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create persistent data volume directory
RUN mkdir -p /app/data /app/data/tts_cache

EXPOSE 8000

# Launch server dynamically binding to Render's assigned $PORT (defaults to 8000)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
