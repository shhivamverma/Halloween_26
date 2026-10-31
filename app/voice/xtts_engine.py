"""Coqui XTTS-v2 zero-shot voice cloning engine adapter."""

import gc
import logging
import os
from pathlib import Path
from typing import List, Optional

from app.voice.base import VoiceSynthesisEngine
from app.voice.watermark import stamp_wav_provenance

logger = logging.getLogger("ofrenda.voice.xtts")

# Automatically acknowledge Coqui Non-Commercial Research License terms
os.environ["COQUI_TOS_AGREED"] = "1"

_xtts_instance = None


class XTTSv2Engine(VoiceSynthesisEngine):
    """Coqui XTTS-v2 cross-lingual zero-shot speech synthesis engine with native Hindi & English support."""

    LANGUAGES = [
        "hi",  # Hindi
        "en",  # English
        "es",  # Spanish
        "fr",  # French
        "de",  # German
        "it",  # Italian
        "pt",  # Portuguese
        "pl",  # Polish
        "tr",  # Turkish
        "ru",  # Russian
        "nl",  # Dutch
        "cs",  # Czech
        "ar",  # Arabic
        "zh-cn",  # Chinese
        "ja",  # Japanese
        "hu",  # Hungarian
        "ko",  # Korean
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
        except Exception as exc:
            self._import_error = str(exc)
            logger.warning("XTTS-v2 dependency import check failed: %s", exc)
            return False

    def _get_model(self):
        """Lazy load XTTS model instance on local CPU or GPU with persistent model caching."""
        global _xtts_instance
        if _xtts_instance is None:
            import torch
            from TTS.api import TTS

            # Limit thread usage on CPU to avoid overloading Render container
            if not torch.cuda.is_available():
                torch.set_num_threads(2)

            use_gpu = torch.cuda.is_available()
            logger.info("Initializing XTTS-v2 model (GPU acceleration: %s)...", use_gpu)

            # Ensure model cache path is persistent if DATA_DIR is set
            data_dir = os.environ.get("DATA_DIR", "")
            if data_dir:
                tts_cache_dir = Path(data_dir) / "tts_cache"
                tts_cache_dir.mkdir(parents=True, exist_ok=True)
                os.environ.setdefault("TTS_HOME", str(tts_cache_dir))

            try:
                _xtts_instance = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=use_gpu)
            except Exception as exc:
                logger.error("Failed to initialize XTTS-v2 model: %s", exc, exc_info=True)
                raise RuntimeError(
                    f"XTTS-v2 model initialization failed: {exc}. "
                    "Ensure adequate persistent disk storage and memory are available."
                ) from exc
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
            err_msg = getattr(self, "_import_error", "torch, torchaudio, or coqui-tts packages could not be imported")
            raise RuntimeError(f"XTTS-v2 dependencies (torch, coqui-tts) are not installed or failed to import: {err_msg}")

        # Map language codes
        lang_code = language.lower()
        if lang_code not in self.LANGUAGES:
            lang_code = "es"

        model = self._get_model()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_out = output_path.with_suffix(".tmp.wav")

        try:
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

            # Compute duration from WAV bytes
            try:
                import soundfile as sf

                info = sf.info(str(output_path))
                duration = round(info.duration, 2)
            except Exception:
                duration = round(len(text.split()) / 2.5, 2)

            return duration
        finally:
            if temp_out.exists():
                try:
                    temp_out.unlink()
                except OSError:
                    pass
            # Trigger garbage collection to free memory on constrained environments
            gc.collect()
