"""Application configuration and environment variables."""

import os
from pathlib import Path


def get_data_dir() -> Path:
    """Return configured DATA_DIR as Path."""
    return Path(os.environ.get("DATA_DIR", "./data"))


def get_ollama_host() -> str:
    """Return configured OLLAMA_HOST."""
    return os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def get_ollama_model() -> str:
    """Return configured default OLLAMA_MODEL."""
    return os.environ.get("OLLAMA_MODEL", "llama3.2:3b")


def get_whisper_model() -> str:
    """Return configured WHISPER_MODEL (tiny: 39 MB RAM for Render Free Tier, or base)."""
    return os.environ.get("WHISPER_MODEL", "tiny")


def get_max_audio_mb() -> int:
    """Return maximum audio upload size in MB."""
    return int(os.environ.get("MAX_AUDIO_MB", 25))


def get_max_photo_mb() -> int:
    """Return maximum photo upload size in MB."""
    return int(os.environ.get("MAX_PHOTO_MB", 8))


def get_llm_timeout_s() -> int:
    """Return LLM request timeout in seconds."""
    return int(os.environ.get("LLM_TIMEOUT_S", 120))


def get_hf_hub_offline() -> bool:
    """Return whether Hugging Face Hub offline mode is active."""
    return os.environ.get("HF_HUB_OFFLINE", "0") in ("1", "true", "True")
