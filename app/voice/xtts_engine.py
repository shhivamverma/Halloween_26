"""Coqui XTTS-v2 zero-shot voice cloning engine adapter."""

import logging
from pathlib import Path
from typing import List, Optional

from app.voice.base import VoiceSynthesisEngine
from app.voice.watermark import stamp_wav_provenance

logger = logging.getLogger("ofrenda.voice.xtts")

_xtts_instance = None


class XTTSv2Engine(VoiceSynthesisEngine):
    """Coqui XTTS-v2 cross-lingual zero-shot speech synthesis engine."""

    LANGUAGES = [
        "es",
        "en",
        "fr",
        "de",
        "it",
        "pt",
        "pl",
        "tr",
        "ru",
        "nl",
        "cs",
        "ar",
        "zh-cn",
        "ja",
        "hu",
        "ko",
        "hi",
    ]

    @property
    def name(self) -> str:
        return "xtts-v2"

    @property
    def supported_languages(self) -> List[str]:
        return self.LANGUAGES

    def is_available(self) -> bool:
        """Check if torch and TTS dependencies are installed."""
        try:
            import torch  # noqa: F401
            import TTS  # noqa: F401

            return True
        except ImportError:
            return False

    def _get_model(self):
        """Lazy load XTTS model instance on local CPU or GPU."""
        global _xtts_instance
        if _xtts_instance is None:
            import torch
            from TTS.api import TTS

            use_gpu = torch.cuda.is_available()
            logger.info("Initializing XTTS-v2 model (GPU acceleration: %s)...", use_gpu)
            _xtts_instance = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=use_gpu)
        return _xtts_instance

    def synthesize(
        self,
        text: str,
        reference_audio_path: Path,
        output_path: Path,
        language: str = "es",
        speed: float = 1.0,
    ) -> float:
        """Synthesize text using reference speaker audio via XTTS-v2."""
        if not self.is_available():
            raise RuntimeError("XTTS-v2 dependencies (torch, TTS) are not installed.")

        # Map language codes
        lang_code = language.lower()
        if lang_code not in self.LANGUAGES:
            lang_code = "es"

        model = self._get_model()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_out = output_path.with_suffix(".tmp.wav")

        model.tts_to_file(
            text=text,
            speaker_wav=str(reference_audio_path),
            language=lang_code,
            file_path=str(temp_out),
            speed=speed,
        )

        # Read, stamp with provenance metadata, and save to final path
        raw_bytes = temp_out.read_bytes()
        watermarked_bytes = stamp_wav_provenance(raw_bytes)
        output_path.write_bytes(watermarked_bytes)

        if temp_out.exists():
            temp_out.unlink()

        # Compute duration from WAV bytes
        try:
            import soundfile as sf

            info = sf.info(str(output_path))
            return round(info.duration, 2)
        except Exception:
            return round(len(text.split()) / 2.5, 2)
