"""Voice synthesis coordination service managing consent, engines, and storage."""

import logging
import os
from pathlib import Path
import time
from typing import Dict, List, Optional

from app.schemas import VoiceConsentRecord, VoiceProfileMetadata
from app.storage import Storage
from app.voice.base import VoiceSynthesisEngine
from app.voice.mock_engine import MockVoiceEngine
from app.voice.openvoice_engine import OpenVoiceEngine
from app.voice.xtts_engine import XTTSv2Engine

logger = logging.getLogger("ofrenda.voice")


class VoiceService:
    """Coordinates local speech synthesis, consent verification, and provenance stamping."""

    def __init__(self):
        self._xtts = XTTSv2Engine()
        self._openvoice = OpenVoiceEngine()
        self._mock = MockVoiceEngine()

    def get_active_engine(self) -> VoiceSynthesisEngine:
        """Return the best available local synthesis engine or test mock."""
        # Check for explicit engine override via environment variable
        override = os.environ.get("VOICE_ENGINE", "").lower()
        if override == "mock":
            return self._mock
        if override == "xtts" and self._xtts.is_available():
            return self._xtts
        if override == "openvoice" and self._openvoice.is_available():
            return self._openvoice

        # Automatic selection: XTTS -> OpenVoice -> Mock (in tests/development)
        if self._xtts.is_available():
            return self._xtts
        if self._openvoice.is_available():
            return self._openvoice

        # Return mock engine for development, demo, and test environments
        return self._mock

    def get_engine_status(self) -> Dict:
        """Report engine status, model name, and supported languages for health checks."""
        engine = self.get_active_engine()
        return {
            "available": True,
            "engine": engine.name,
            "active_engine": engine.name,
            "supported_languages": engine.supported_languages,
        }

    def process_and_save_reference(
        self,
        ofrenda_id: str,
        audio_bytes: bytes,
        ext: str,
        consent: VoiceConsentRecord,
        storage: Storage,
    ) -> VoiceProfileMetadata:
        """Verify affirmative consent, save reference audio, and record audit log."""
        if not consent.confirmed_permission:
            raise ValueError("Affirmative family authorization is strictly required to process reference audio.")

        # Estimate duration
        approx_duration = max(2.0, round(len(audio_bytes) / 32000.0, 2))

        record = storage.save_voice_reference(
            ofrenda_id=ofrenda_id,
            audio_bytes=audio_bytes,
            ext=ext,
            consent=consent,
            duration_s=approx_duration,
        )
        return record.voice_profile

    def synthesize_remembrance(
        self,
        ofrenda_id: str,
        language: str,
        speed: float,
        consent: VoiceConsentRecord,
        storage: Storage,
    ) -> VoiceProfileMetadata:
        """Synthesize remembrance speech using reference voice."""
        if not consent.confirmed_permission:
            raise ValueError("Explicit family authorization is strictly required for voice synthesis.")

        record = storage.get(ofrenda_id)
        if not record:
            raise KeyError(f"Ofrenda {ofrenda_id} not found")

        ref_path = storage.get_reference_audio_path(ofrenda_id)
        if not ref_path or not ref_path.exists():
            raise ValueError("No reference voice audio found. Please upload family-authorized reference audio first.")

        remembrance_text = (record.remembrance or "").strip()
        if not remembrance_text:
            raise ValueError("No remembrance text found. Please generate a remembrance before creating voice recreation.")

        engine = self.get_active_engine()

        # Validate language support
        lang = language.lower()
        if lang not in engine.supported_languages:
            lang = "es" if "es" in engine.supported_languages else engine.supported_languages[0]

        voice_folder = storage.get_voice_folder(ofrenda_id)
        out_wav_path = voice_folder / "remembrance_synthesized.wav"

        start_t = time.perf_counter()
        duration_s = engine.synthesize(
            text=remembrance_text,
            reference_audio_path=ref_path,
            output_path=out_wav_path,
            language=lang,
            speed=speed,
        )
        elapsed = time.perf_counter() - start_t
        logger.info(
            "Synthesized voice recreation with %s in %.2fs (audio duration: %.2fs)",
            engine.name,
            elapsed,
            duration_s,
        )

        from app.voice.watermark import stamp_wav_provenance

        watermarked_wav = stamp_wav_provenance(
            out_wav_path.read_bytes(),
            authorized_by=consent.authorized_by,
            deceased_name=record.name,
            model_name=engine.name,
        )

        record = storage.save_synthesized_voice(
            ofrenda_id=ofrenda_id,
            wav_bytes=watermarked_wav,
            model_used=engine.name,
            language=lang,
            duration_s=duration_s,
        )
        return record.voice_profile


_voice_service_singleton = None


def get_voice_service() -> VoiceService:
    """Return singleton VoiceService instance."""
    global _voice_service_singleton
    if _voice_service_singleton is None:
        _voice_service_singleton = VoiceService()
    return _voice_service_singleton
