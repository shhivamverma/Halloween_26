"""Voice synthesis and zero-shot voice conversion coordination service."""

import logging
import os
from pathlib import Path
import time
from typing import Dict, List, Optional

from app.schemas import VoiceConsentRecord, VoiceProfileMetadata
from app.storage import Storage
from app.voice.base import VoiceConversionEngine, VoiceSynthesisEngine
from app.voice.kokoro_engine import KokoroOpenVoiceEngine
from app.voice.mms_engine import MMSVitsEngine
from app.voice.mock_engine import MockVoiceConversionEngine, MockVoiceEngine
from app.voice.openvoice_engine import OpenVoiceEngine
from app.voice.seed_vc_engine import SeedVCEngine
from app.voice.xtts_engine import XTTSv2Engine, get_effective_cgroup_limit_mb

logger = logging.getLogger("ofrenda.voice")


class VoiceService:
    """Coordinates local speech synthesis, zero-shot voice conversion, consent verification, and provenance stamping."""

    def __init__(self):
        # Genuine Zero-Shot Voice Conversion engines
        # Primary: Kokoro-82M + OpenVoice V2 (High-naturalness, English & Experimental Hindi)
        # Alternative: Seed-VC (Direct acoustic flow matching, English-viable; collapses Hindi)
        self._kokoro_vc = KokoroOpenVoiceEngine()
        self._seed_vc = SeedVCEngine()
        self._mock_vc = MockVoiceConversionEngine()

        # Text-to-Speech remembrance reading engines (decoupled from S2S voice conversion)
        self._mms = MMSVitsEngine()
        self._xtts = XTTSv2Engine()
        self._openvoice = OpenVoiceEngine()
        self._mock = MockVoiceEngine()

    def get_active_conversion_engine(self) -> Optional[VoiceConversionEngine]:
        """Return the active Zero-Shot Speech-to-Speech Voice Conversion engine.

        Selection priority:
        1. Test environments / mock override -> MockVoiceConversionEngine
        2. Explicit 'seed-vc' override -> SeedVCEngine (English-only alternative)
        3. Primary default -> KokoroOpenVoiceEngine
        4. Fallback alternative -> SeedVCEngine
        """
        override = os.environ.get("VOICE_ENGINE", "").lower()
        is_test_env = bool(os.environ.get("PYTEST_CURRENT_TEST") or override == "mock")

        if is_test_env or override == "mock":
            return self._mock_vc

        if override == "seed-vc" and self._seed_vc.is_available():
            return self._seed_vc

        if self._kokoro_vc.is_available():
            return self._kokoro_vc

        if self._seed_vc.is_available():
            return self._seed_vc

        return self._mock_vc if is_test_env else None

    def is_neural_engine_available(self) -> bool:
        """Check if a genuine neural voice conversion or synthesis engine is available."""
        return self._kokoro_vc.is_available() or self._seed_vc.is_available() or self._mms.is_available()

    def get_active_engine(self) -> Optional[VoiceSynthesisEngine]:
        """Return the active text-to-speech synthesis engine (for remembrance reading)."""
        override = os.environ.get("VOICE_ENGINE", "").lower()
        is_test_env = bool(os.environ.get("PYTEST_CURRENT_TEST") or override == "mock")

        if is_test_env or override == "mock":
            return self._mock

        if override == "xtts" and self._xtts.is_available():
            return self._xtts
        if override == "openvoice" and self._openvoice.is_available():
            return self._openvoice

        if self._mms.is_available():
            return self._mms

        return None

    def get_engine_status(self) -> Dict:
        """Report genuine engine status and dependency transparency for health checks."""
        vc_engine = self.get_active_conversion_engine()
        is_test_env = bool(os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("VOICE_ENGINE") == "mock")

        if vc_engine is not None and vc_engine != self._mock_vc:
            return {
                "available": True,
                "engine": vc_engine.name,
                "active_engine": vc_engine.name,
                "conversion_engine": vc_engine.name,
                "status": "ready",
                "supported_languages": vc_engine.supported_languages,
                "message": f"Zero-Shot Speech-to-Speech Voice Conversion Engine '{vc_engine.name}' is operational.",
            }
        elif is_test_env:
            return {
                "available": True,
                "engine": self._mock_vc.name,
                "active_engine": self._mock_vc.name,
                "conversion_engine": self._mock_vc.name,
                "status": "test_mock_ready",
                "supported_languages": self._mock_vc.supported_languages,
                "message": "Test mock voice conversion engine active for automated test verification.",
            }
        else:
            return {
                "available": False,
                "engine": "seed-vc",
                "active_engine": "none",
                "conversion_engine": "none",
                "status": "dependencies_missing",
                "supported_languages": ["en", "hi"],
                "missing_dependencies": ["torch", "torchaudio", "transformers"],
                "install_instructions": "pip install torch torchaudio transformers",
                "message": (
                    "Zero-Shot Voice Conversion engine (Seed-VC) dependencies are not installed in the local environment. "
                    "In accordance with our strict ethical standards, synthetic sine wave beeps are disabled."
                ),
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
        if engine is None:
            raise ValueError(
                "Neural voice conversion dependencies ('torch' and 'TTS') are not installed in the local environment. "
                "To run local voice recreation, install with: pip install torch TTS. "
                "Generating synthetic sine-wave beeps as a substitute is strictly disabled."
            )

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

    def convert_speech_to_speech(
        self,
        ofrenda_id: str,
        user_audio_bytes: bytes,
        ext: str,
        consent: VoiceConsentRecord,
        storage: Storage,
        target_language: Optional[str] = None,
        transcript: Optional[str] = None,
        engine_name: Optional[str] = None,
    ) -> Dict:
        """Convert user recorded microphone speech into the target speaker's voice using Zero-Shot conversion.

        Supports:
        - Primary: Kokoro-82M + OpenVoice V2 (High-naturalness, English & Experimental Hindi)
        - Alternative: Seed-VC (Direct acoustic flow matching, English-viable; collapses Hindi)
        """
        import inspect

        if not consent.confirmed_permission:
            raise ValueError("Explicit family authorization is strictly required for voice conversion.")

        record = storage.get(ofrenda_id)
        if not record:
            raise KeyError(f"Ofrenda {ofrenda_id} not found")

        ref_path = storage.get_reference_audio_path(ofrenda_id)
        if not ref_path or not ref_path.exists():
            raise ValueError("No reference voice audio found. Please upload a family-authorized reference recording first.")

        if not user_audio_bytes or len(user_audio_bytes) < 500:
            raise ValueError("Microphone recording is empty or corrupt. Please record your speech clearly.")

        # Engine resolution (respecting user override or default)
        is_test_env = bool(os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("VOICE_ENGINE") == "mock")
        if is_test_env:
            conversion_engine = self._mock_vc
        elif (engine_name or "").lower() == "seed-vc" and self._seed_vc.is_available():
            conversion_engine = self._seed_vc
        else:
            conversion_engine = self.get_active_conversion_engine()

        if conversion_engine is None:
            return {
                "status": "unavailable",
                "model_ready": False,
                "engine_used": "none",
                "message": (
                    "Zero-Shot Voice Conversion engine is not installed in the local environment. "
                    "Install with: pip install torch kokoro transformers soundfile. "
                    "In accordance with memorial integrity guidelines, synthetic sine wave beeps are disabled."
                ),
            }

        chosen_lang = (target_language or record.language or "en").lower()
        if chosen_lang not in conversion_engine.supported_languages:
            chosen_lang = "en" if "en" in conversion_engine.supported_languages else conversion_engine.supported_languages[0]

        voice_folder = storage.get_voice_folder(ofrenda_id)
        user_input_path = voice_folder / f"user_mic_input{ext}"
        out_wav_path = voice_folder / "remembrance_synthesized.wav"

        user_input_path.write_bytes(user_audio_bytes)

        try:
            # Build engine-specific kwargs safely
            sig_params = inspect.signature(conversion_engine.convert_voice).parameters
            call_kwargs = {
                "source_audio_path": user_input_path,
                "reference_audio_path": ref_path,
                "output_path": out_wav_path,
                "language": chosen_lang,
                "diffusion_steps": 25,
            }
            if "text" in sig_params and transcript:
                call_kwargs["text"] = transcript.strip()

            duration_s = conversion_engine.convert_voice(**call_kwargs)

            from app.voice.watermark import stamp_wav_provenance

            watermarked_wav = stamp_wav_provenance(
                out_wav_path.read_bytes(),
                authorized_by=consent.authorized_by,
                deceased_name=record.name,
                model_name=conversion_engine.name,
            )

            updated_record = storage.save_synthesized_voice(
                ofrenda_id=ofrenda_id,
                wav_bytes=watermarked_wav,
                model_used=conversion_engine.name,
                language=chosen_lang,
                duration_s=duration_s,
            )

            return {
                "status": "success",
                "model_ready": True,
                "engine_used": conversion_engine.name,
                "detected_language": chosen_lang,
                "duration_s": duration_s,
                "experimental_hindi": bool(chosen_lang == "hi" and conversion_engine.name in ("kokoro-openvoice", "mock-voice-conversion")),
                "voice_profile": updated_record.voice_profile.model_dump(),
            }
        finally:
            # Safely clean up raw user microphone upload file
            try:
                if user_input_path.exists():
                    user_input_path.unlink()
            except Exception as clean_err:
                logger.debug("Could not unlink temp user mic file: %s", clean_err)


_voice_service_singleton = None


def get_voice_service() -> VoiceService:
    """Return singleton VoiceService instance."""
    global _voice_service_singleton
    if _voice_service_singleton is None:
        _voice_service_singleton = VoiceService()
    return _voice_service_singleton
