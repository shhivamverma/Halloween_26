"""Local speech-to-text transcription using faster-whisper."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import get_whisper_model

_model = None


def get_whisper_model_instance():
    """Lazy load singleton WhisperModel instance on CPU with int8 quantization."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        model_size = get_whisper_model()
        _model = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _model


def transcribe(path: str | Path, language_hint: Optional[str] = None) -> Dict[str, Any]:
    """Transcribe audio file at path locally using faster-whisper.

    Returns dict with keys: text, language, duration.
    """
    model = get_whisper_model_instance()
    # If language_hint is valid (e.g. 'en' or 'es'), guide Whisper; otherwise let it detect
    lang = language_hint if language_hint in ("en", "es") else None

    segments, info = model.transcribe(str(path), language=lang, beam_size=5)

    collected_segments = [s.text.strip() for s in segments]
    full_text = " ".join([seg for seg in collected_segments if seg]).strip()

    detected_lang = info.language if info and info.language else (language_hint or "en")
    duration_s = round(info.duration, 2) if info and info.duration else 0.0

    return {
        "text": full_text,
        "language": detected_lang,
        "duration": duration_s,
    }
