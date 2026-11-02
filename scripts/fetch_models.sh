#!/usr/bin/env bash
set -e

echo "Pulling Ollama default model (llama3.2:3b)..."
ollama pull llama3.2:3b || echo "Ollama not running or not installed, skipping Ollama pull (template fallback will be used)."

echo "Warming faster-whisper tiny & base model cache..."
python -c "from faster_whisper import WhisperModel; WhisperModel('tiny', device='cpu')"

echo "Warming Kokoro-82M model cache..."
python -c "from kokoro import KPipeline; KPipeline(lang_code='a', device='cpu'); KPipeline(lang_code='h', device='cpu')"

echo "Warming OpenVoice V2 model cache..."
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('myshell-ai/OpenVoiceV2', 'converter/checkpoint.pth'); hf_hub_download('myshell-ai/OpenVoiceV2', 'converter/config.json')"

echo "Models downloaded and cached successfully. Set HF_HUB_OFFLINE=1 for pure offline mode."
