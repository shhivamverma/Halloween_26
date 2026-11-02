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


def get_server_host() -> str:
    """Return server host binding. Defaults to 127.0.0.1 (secure loopback).

    LAN exposure (0.0.0.0) requires explicit ALLOW_LAN=1 or HOST=0.0.0.0.
    """
    if os.environ.get("ALLOW_LAN", "0") in ("1", "true", "True"):
        return "0.0.0.0"
    return os.environ.get("HOST", "127.0.0.1")


def get_server_port() -> int:
    """Return server port. Defaults to 8000."""
    return int(os.environ.get("PORT", 8000))
