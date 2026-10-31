"""Coqui XTTS-v2 zero-shot voice cloning engine adapter."""

import gc
import logging
import os
from pathlib import Path
import threading
import time
from typing import List, Optional

from app.voice.base import VoiceSynthesisEngine
from app.voice.watermark import stamp_wav_provenance

logger = logging.getLogger("ofrenda.voice.xtts")

# Automatically acknowledge Coqui Non-Commercial Research License terms
os.environ["COQUI_TOS_AGREED"] = "1"

_init_lock = threading.Lock()
_xtts_instance = None
_audio_loader_patched = False


def _patch_torchaudio_loader_if_needed():
    """Ensure torchaudio can safely load audio files even if torchcodec dynamic libraries are missing."""
    global _audio_loader_patched
    if _audio_loader_patched:
        return
    try:
        import soundfile as sf
        import torch
        import torchaudio

        orig_load = torchaudio.load

        def safe_load(filepath, *args, **kwargs):
            try:
                return orig_load(filepath, *args, **kwargs)
            except Exception:
                data, sr = sf.read(str(filepath), dtype="float32")
                tensor = torch.from_numpy(data)
                if tensor.ndim == 1:
                    tensor = tensor.unsqueeze(0)
                elif tensor.ndim == 2:
                    tensor = tensor.t()
                return tensor, sr

        torchaudio.load = safe_load
        _audio_loader_patched = True
        logger.debug("Configured safe audio loader fallback using soundfile.")
    except Exception as exc:
        logger.debug("Audio loader patch skipped: %s", exc)


def get_system_resources() -> dict:
    """Inspect system RAM and disk availability for model inference."""
    try:
        import psutil

        vm = psutil.virtual_memory()
        data_dir = os.environ.get("DATA_DIR", ".")
        disk = psutil.disk_usage(data_dir if Path(data_dir).exists() else ".")
        return {
            "ram_total_mb": round(vm.total / (1024 * 1024), 1),
            "ram_available_mb": round(vm.available / (1024 * 1024), 1),
            "disk_free_mb": round(disk.free / (1024 * 1024), 1),
        }
    except Exception:
        return {"ram_total_mb": 0.0, "ram_available_mb": 0.0, "disk_free_mb": 0.0}


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

    REQUIRED_MODEL_FILES = ["model.pth", "config.json", "vocab.json", "speakers_xtts.pth"]

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

    def _configure_cache_paths(self):
        """Configure persistent model caching directories."""
        data_dir = os.environ.get("DATA_DIR")
        if not data_dir:
            data_dir = str(Path("data").resolve())
        tts_home = os.environ.get("TTS_HOME") or str(Path(data_dir) / "tts_cache")
        hf_home = os.environ.get("HF_HOME") or str(Path(data_dir) / "hf_home")
        hf_hub_cache = os.environ.get("HF_HUB_CACHE") or str(Path(hf_home) / "hub")

        os.environ["TTS_HOME"] = tts_home
        os.environ["HF_HOME"] = hf_home
        os.environ["HF_HUB_CACHE"] = hf_hub_cache

        Path(tts_home).mkdir(parents=True, exist_ok=True)
        Path(hf_home).mkdir(parents=True, exist_ok=True)
        Path(hf_hub_cache).mkdir(parents=True, exist_ok=True)

    def _get_model(self):
        """Thread-safe singleton loading of XTTS-v2 model instance with persistent model caching."""
        global _xtts_instance
        if _xtts_instance is not None:
            return _xtts_instance

        with _init_lock:
            if _xtts_instance is not None:
                return _xtts_instance

            _patch_torchaudio_loader_if_needed()
            self._configure_cache_paths()

            res = get_system_resources()
            logger.info(
                "XTTS-v2 initialization starting (RAM available: %.0fMB / %.0fMB, Disk free: %.0fMB)...",
                res["ram_available_mb"],
                res["ram_total_mb"],
                res["disk_free_mb"],
            )

            # Ensure online lookups are enabled during model download and verification
            os.environ["HF_HUB_OFFLINE"] = "0"

            import torch
            from TTS.api import TTS

            # Limit thread usage on CPU to avoid overloading Render container
            use_gpu = torch.cuda.is_available()
            if not use_gpu:
                torch.set_num_threads(2)

            start_t = time.perf_counter()
            try:
                logger.info("Initializing XTTS-v2 model (model_name='tts_models/multilingual/multi-dataset/xtts_v2', gpu=%s)...", use_gpu)
                _xtts_instance = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=use_gpu)
                elapsed = time.perf_counter() - start_t
                logger.info("XTTS-v2 model successfully initialized and cached in %.2fs.", elapsed)

                # Once verified and downloaded, enable offline mode to prevent unexpected network calls
                os.environ["HF_HUB_OFFLINE"] = "1"
            except MemoryError as mem_err:
                logger.error("Out of memory while loading XTTS-v2 model: %s", mem_err)
                raise RuntimeError(
                    f"XTTS-v2 model initialization failed due to memory constraints (Available RAM: {res['ram_available_mb']:.0f}MB). "
                    "Loading the 1.8GB neural weights requires at least 2GB of RAM. "
                    "Render Free Tier instances provide 512MB RAM; please upgrade to a Starter (2GB) or Standard plan."
                ) from mem_err
            except Exception as exc:
                logger.error("Failed to initialize XTTS-v2 model: %s", exc, exc_info=True)
                raise RuntimeError(
                    f"XTTS-v2 model initialization failed: {exc}. "
                    f"System state: {res['ram_available_mb']:.0f}MB RAM available, {res['disk_free_mb']:.0f}MB disk free. "
                    "Ensure adequate persistent storage and network access for initial model download."
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
