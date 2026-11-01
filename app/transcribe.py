"""Local speech-to-text transcription using faster-whisper."""

import logging
import os
from pathlib import Path
import time
from typing import Any, Dict, Optional

from app.config import get_whisper_model

logger = logging.getLogger("ofrenda.transcribe")
_model = None


def get_whisper_model_instance():
    """Lazy load singleton WhisperModel instance on CPU with int8 quantization.

    Attempts local-only offline loading first to prevent hanging on Hugging Face network checks.
    """
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        model_size = get_whisper_model()
        try:
            _model = WhisperModel(model_size, device="cpu", compute_type="int8", local_files_only=True)
            logger.info("Loaded Whisper model '%s' offline with local_files_only=True", model_size)
        except Exception as exc:
            logger.info("Whisper offline load failed (%s), fetching model...", exc)
            _model = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _model


def transcribe(path: str | Path, language_hint: Optional[str] = None) -> Dict[str, Any]:
    """Transcribe audio file at path locally using faster-whisper.

    Returns dict with keys: text, language, duration. Logs timing only, never content.
    """
    start_t = time.perf_counter()
    model = get_whisper_model_instance()
    lang = language_hint if language_hint in ("en", "es", "hi") else None

    segments, info = model.transcribe(str(path), language=lang, beam_size=5)

    collected_segments = [s.text.strip() for s in segments]
    full_text = " ".join([seg for seg in collected_segments if seg]).strip()

    detected_lang = info.language if info and info.language else (language_hint or "en")
    duration_s = round(info.duration, 2) if info and info.duration else 0.0

    elapsed = time.perf_counter() - start_t
    rtfx = duration_s / elapsed if elapsed > 0 else 0.0
    logger.info("Transcribed audio duration %.2fs in %.2fs (RTFx: %.2f)", duration_s, elapsed, rtfx)

    return {
        "text": full_text,
        "language": detected_lang,
        "duration": duration_s,
    }
