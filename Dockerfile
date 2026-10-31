# Multi-stage production Dockerfile for Offline Ofrenda Keeper
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    OLLAMA_HOST=http://host.docker.internal:11434 \
    WHISPER_MODEL=tiny \
    HF_HOME=/app/data/hf_home \
    HF_HUB_CACHE=/app/data/hf_home/hub \
    TTS_HOME=/app/data/tts_cache \
    COQUI_TOS_AGREED=1 \
    HF_HUB_OFFLINE=0

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

# Pre-download and cache faster-whisper model (tiny: 39 MB RAM) so container starts fast
RUN python3 -c "from faster_whisper import WhisperModel; WhisperModel('tiny', device='cpu', compute_type='int8')"

# Pre-download and cache lightweight MMS-TTS models (Hindi, English, Spanish) for Render Free Tier (512MB RAM)
RUN python3 -c "from transformers import VitsModel, AutoTokenizer; \
    AutoTokenizer.from_pretrained('facebook/mms-tts-eng'); VitsModel.from_pretrained('facebook/mms-tts-eng'); \
    AutoTokenizer.from_pretrained('facebook/mms-tts-hin'); VitsModel.from_pretrained('facebook/mms-tts-hin'); \
    AutoTokenizer.from_pretrained('facebook/mms-tts-spa'); VitsModel.from_pretrained('facebook/mms-tts-spa')"

# Copy application source code
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create persistent data volume directories
RUN mkdir -p /app/data /app/data/tts_cache /app/data/hf_home /app/data/hf_home/hub

EXPOSE 8000

# Launch server dynamically binding to Render's assigned $PORT (defaults to 8000)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
