#!/usr/bin/env bash
set -e

echo "Pulling Ollama default model (llama3.2:3b)..."
ollama pull llama3.2:3b

echo "Warming faster-whisper base model cache..."
python -c "from faster_whisper import WhisperModel; WhisperModel('base')"

echo "Models downloaded successfully. Set HF_HUB_OFFLINE=1 for offline mode."
