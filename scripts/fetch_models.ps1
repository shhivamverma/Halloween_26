# Pre-download and cache models for Offline Ofrenda Keeper on Windows
$ErrorActionPreference = "Continue"

Write-Host "Checking local Ollama model (llama3.2:3b)..." -ForegroundColor Cyan
try {
    ollama pull llama3.2:3b
} catch {
    Write-Host "Ollama not running or not installed. The app will use the built-in procedural template fallback." -ForegroundColor Yellow
}

Write-Host "Warming faster-whisper model cache..." -ForegroundColor Cyan
& python -c "from faster_whisper import WhisperModel; WhisperModel('tiny', device='cpu')"

Write-Host "Warming Kokoro-82M model cache (English & Hindi)..." -ForegroundColor Cyan
& python -c "from kokoro import KPipeline; KPipeline(lang_code='a', device='cpu'); KPipeline(lang_code='h', device='cpu')"

Write-Host "Warming OpenVoice V2 model cache..." -ForegroundColor Cyan
& python -c "from huggingface_hub import hf_hub_download; hf_hub_download('myshell-ai/OpenVoiceV2', 'converter/checkpoint.pth'); hf_hub_download('myshell-ai/OpenVoiceV2', 'converter/config.json')"

Write-Host "Models successfully cached! Set `$env:HF_HUB_OFFLINE='1' for pure offline operation." -ForegroundColor Green

