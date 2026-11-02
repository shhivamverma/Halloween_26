"""Kokoro-82M + OpenVoice V2 Voice Conversion Engine Adapter.

Implements zero-shot voice conversion combining:
1. Native language text-to-speech via Kokoro-82M (StyleTTS 2 + ISTFTNet).
   - English ('a'): Expressive, human-grade natural speech ('af_heart', 'am_adam').
   - Hindi ('h'): Native G2P phonemization ('hf_alpha', 'hm_omega').
2. Decoupled vocal timbre adaptation via OpenVoice V2 ToneColorConverter.
   - Dual speaker embedding extraction: source style vector (src_se) from Kokoro base
     and target reference speaker style vector (tgt_se) from authorized reference audio.
   - Conditioning normalizing flow strictly on both vectors to transfer vocal timbre.

Note: Hindi OpenVoice conversion is marked as EXPERIMENTAL. While Kokoro produces native
Hindi pronunciation, OpenVoice was trained on English/CJK corpora and may introduce vocoder
acoustic artifacts on non-native phonemes.
"""

import gc
import logging
from pathlib import Path
import time
from typing import Dict, List, Optional

import numpy as np
import soundfile as sf
import torch

from app.voice.base import VoiceConversionEngine
from app.voice.watermark import stamp_wav_provenance

logger = logging.getLogger("ofrenda.voice.kokoro_openvoice")


class KokoroOpenVoiceEngine(VoiceConversionEngine):
    """Primary zero-shot voice conversion engine using Kokoro-82M and OpenVoice V2."""

    OPENVOICE_REPO = "myshell-ai/OpenVoiceV2"
    KOKORO_REPO = "hexgrad/Kokoro-82M"

    # Default voice profiles per language
    VOICE_CONFIG = {
        "en": {
            "lang_code": "a",
            "female_voice": "af_heart",
            "male_voice": "am_adam",
            "default_voice": "af_heart",
        },
        "hi": {
            "lang_code": "h",
            "female_voice": "hf_alpha",
            "male_voice": "hm_omega",
            "default_voice": "hf_alpha",
            "experimental": True,
        },
    }

    def __init__(self, device: Optional[str] = None):
        self._device = device or "cpu"
        self._kokoro_pipelines: Dict[str, any] = {}
        self._openvoice_converter = None
        self._whisper = None
        self._initialized = False

    @property
    def name(self) -> str:
        return "kokoro-openvoice"

    @property
    def supported_languages(self) -> List[str]:
        return ["en", "hi"]

    def is_available(self) -> bool:
        """Check if kokoro and openvoice dependencies are installed."""
        try:
            import kokoro  # noqa: F401
            import librosa  # noqa: F401
            from faster_whisper import WhisperModel  # noqa: F401
            self._ensure_openvoice_in_syspath()
            from modules.openvoice.api import ToneColorConverter  # noqa: F401

            return True
        except ImportError:
            return False

    @staticmethod
    def _ensure_openvoice_in_syspath():
        import sys
        tmp_path = str(Path(__file__).resolve().parent.parent.parent / "tmp_seed_vc")
        if tmp_path not in sys.path:
            sys.path.append(tmp_path)

    def _get_kokoro_pipeline(self, lang_code: str):
        """Lazy-load and cache KPipeline instance per language."""
        if lang_code not in self._kokoro_pipelines:
            from kokoro import KPipeline

            logger.info("Initializing Kokoro KPipeline for lang_code='%s' on %s...", lang_code, self._device)
            self._kokoro_pipelines[lang_code] = KPipeline(lang_code=lang_code, repo_id=self.KOKORO_REPO)
        return self._kokoro_pipelines[lang_code]

    def _get_openvoice_converter(self):
        """Lazy-load and cache OpenVoice V2 ToneColorConverter."""
        if self._openvoice_converter is None:
            self._ensure_openvoice_in_syspath()
            from huggingface_hub import hf_hub_download
            from modules.openvoice.api import ToneColorConverter

            logger.info("Loading OpenVoice V2 Converter on %s...", self._device)
            ckpt_path = hf_hub_download(repo_id=self.OPENVOICE_REPO, filename="converter/checkpoint.pth")
            config_path = hf_hub_download(repo_id=self.OPENVOICE_REPO, filename="converter/config.json")
            converter = ToneColorConverter(config_path, device=self._device)
            converter.load_ckpt(ckpt_path)
            self._openvoice_converter = converter
        return self._openvoice_converter

    def _get_whisper(self):
        """Lazy-load faster-whisper instance for speech transcription fallback."""
        if self._whisper is None:
            from faster_whisper import WhisperModel

            logger.info("Loading faster-whisper model for ASR transcription...")
            self._whisper = WhisperModel("base", device="cpu", compute_type="int8")
        return self._whisper

    def convert_voice(
        self,
        source_audio_path: Path,
        reference_audio_path: Path,
        output_path: Path,
        language: Optional[str] = "en",
        diffusion_steps: int = 25,
        text: Optional[str] = None,
        voice_id: Optional[str] = None,
    ) -> float:
        """Execute full voice conversion: Transcript -> Kokoro Speech -> OpenVoice Tone Transfer.

        Args:
            source_audio_path: User recorded speech WAV (for ASR if text is not provided).
            reference_audio_path: Memorial reference voice recording (timbre to clone).
            output_path: Destination WAV path.
            language: Language code ('en' or 'hi').
            diffusion_steps: Unused in Kokoro/OpenVoice, preserved for interface compatibility.
            text: Optional pre-reviewed transcript text. If None, runs ASR on source_audio_path.
            voice_id: Optional Kokoro base voice override (e.g. 'af_heart', 'hf_alpha').

        Returns:
            Duration of converted audio in seconds.
        """
        import librosa

        start_t = time.perf_counter()
        lang = (language or "en").lower()
        if lang not in self.VOICE_CONFIG:
            lang = "en"

        cfg = self.VOICE_CONFIG[lang]
        if cfg.get("experimental"):
            logger.warning("Executing EXPERIMENTAL Hindi OpenVoice conversion. Vocoder artifacts may occur.")

        # 1. Step 1: Obtain Transcript (Use provided reviewed text, or transcribe via Whisper)
        transcript_text = (text or "").strip()
        if not transcript_text:
            whisper = self._get_whisper()
            init_prompt = "नमस्ते, यह हिंदी में है।" if lang == "hi" else None
            segs, info = whisper.transcribe(
                str(source_audio_path),
                language="hi" if lang == "hi" else "en",
                initial_prompt=init_prompt,
                beam_size=5,
            )
            transcript_text = " ".join([s.text for s in segs]).strip()

        if not transcript_text:
            raise ValueError("No speech content could be transcribed from the source recording.")

        logger.info("Kokoro base synthesis text: \"%s\" (lang: %s)", transcript_text, lang)

        # 2. Step 2: Synthesize Base Natural Speech via Kokoro-82M KPipeline
        pipeline = self._get_kokoro_pipeline(cfg["lang_code"])
        selected_voice = voice_id or cfg["default_voice"]

        chunks = []
        for gs, ps, audio in pipeline(transcript_text, voice=selected_voice, speed=1.0):
            if audio is not None:
                if isinstance(audio, torch.Tensor):
                    audio = audio.detach().cpu().numpy()
                chunks.append(np.asarray(audio, dtype=np.float32))

        if not chunks:
            raise RuntimeError(f"Kokoro-82M generated empty audio for text: '{transcript_text}'")

        kokoro_audio_24k = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
        kokoro_audio_24k = np.asarray(kokoro_audio_24k, dtype=np.float32)

        # 3. Step 3: Resample Kokoro Audio to 22,050 Hz for OpenVoice
        kokoro_audio_22k = librosa.resample(kokoro_audio_24k, orig_sr=24000, target_sr=22050)
        src_tensor = torch.from_numpy(kokoro_audio_22k).float()

        # 4. Step 4: Load & Resample Target Reference Audio to 22,050 Hz
        ref_data, ref_sr = sf.read(str(reference_audio_path), dtype="float32")
        if ref_data.ndim > 1:
            ref_data = ref_data.mean(axis=1)
        if ref_sr != 22050:
            ref_data = librosa.resample(ref_data, orig_sr=ref_sr, target_sr=22050)
        ref_tensor = torch.from_numpy(ref_data).float()

        # 5. Step 5: Extract Dual Embeddings & Apply ToneColorConverter
        converter = self._get_openvoice_converter()
        src_se = converter.extract_se([src_tensor], [len(src_tensor)])
        tgt_se = converter.extract_se([ref_tensor], [len(ref_tensor)])

        converted_tensor = converter.convert(
            src_waves=src_tensor.unsqueeze(0),
            src_wave_lengths=torch.tensor([len(src_tensor)]),
            src_se=src_se,
            tgt_se=tgt_se,
            tau=0.3,
        )
        converted_np = converted_tensor.squeeze().cpu().numpy()

        # Peak normalization to prevent digital distortion
        max_val = np.max(np.abs(converted_np))
        if max_val > 0.95:
            converted_np = converted_np * (0.95 / max_val)

        # 6. Step 6: Save Converted Audio & Stamp Provenance
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_path), converted_np, 22050, subtype="PCM_16")

        # Stamp RIFF provenance metadata certifying AI voice simulation
        raw_bytes = output_path.read_bytes()
        watermarked_bytes = stamp_wav_provenance(raw_bytes, model_name=self.name)
        output_path.write_bytes(watermarked_bytes)

        # 7. CPU Memory Cleanup: Release intermediate tensor allocations
        del chunks, kokoro_audio_24k, kokoro_audio_22k, src_tensor, ref_data, ref_tensor, converted_tensor, converted_np
        gc.collect()

        out_info = sf.info(str(output_path))
        duration = round(float(out_info.duration), 2)
        elapsed = time.perf_counter() - start_t
        logger.info(
            "Kokoro + OpenVoice conversion complete in %.2fs (duration: %.2fs, lang: %s, experimental_hindi: %s)",
            elapsed,
            duration,
            lang,
            bool(cfg.get("experimental")),
        )
        return duration
