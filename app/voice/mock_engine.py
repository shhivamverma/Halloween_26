"""Mock voice synthesis engine for lightning-fast testing and fallback environments."""

import math
from pathlib import Path
import struct
from typing import List

from app.voice.base import VoiceConversionEngine, VoiceSynthesisEngine
from app.voice.watermark import stamp_wav_provenance


class MockVoiceEngine(VoiceSynthesisEngine):
    """Generates synthetic tone WAV audio in milliseconds without requiring neural checkpoints."""

    @property
    def name(self) -> str:
        return "mock-voice-engine"

    @property
    def supported_languages(self) -> List[str]:
        return ["es", "en", "hi", "fr", "de", "it", "pt"]

    def is_available(self) -> bool:
        return True

    def synthesize(
        self,
        text: str,
        reference_audio_path: Path,
        output_path: Path,
        language: str = "es",
        speed: float = 1.0,
    ) -> float:
        """Generate a valid, watermarked WAV file simulating speech synthesis."""
        sample_rate = 22050
        # Estimate duration from word count (approx 130 words per minute / speed)
        words = len(text.split()) if text else 10
        raw_duration = max(1.5, min(15.0, (words / 2.5) / max(0.5, speed)))
        duration = round(raw_duration, 2)
        total_samples = int(sample_rate * duration)

        # Generate a soft harmonic chime / chord wave
        samples = []
        for i in range(total_samples):
            t = i / sample_rate
            # 220Hz + 440Hz warm chime with exponential decay envelope
            envelope = math.exp(-t / (duration * 0.75))
            val = (0.5 * math.sin(2 * math.pi * 220 * t) + 0.3 * math.sin(2 * math.pi * 440 * t)) * envelope
            pcm_val = max(-32767, min(32767, int(val * 18000)))
            samples.append(pcm_val)

        raw_pcm = struct.pack(f"<{len(samples)}h", *samples)

        # Build WAV headers
        num_channels = 1
        bytes_per_sample = 2
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        data_size = len(raw_pcm)

        header = (
            b"RIFF"
            + struct.pack("<I", 36 + data_size)
            + b"WAVE"
            + b"fmt "
            + struct.pack("<IHHIIHH", 16, 1, num_channels, sample_rate, byte_rate, block_align, 16)
            + b"data"
            + struct.pack("<I", data_size)
        )

        wav_bytes = header + raw_pcm
        watermarked_bytes = stamp_wav_provenance(wav_bytes)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(watermarked_bytes)

        return duration


class MockVoiceConversionEngine(VoiceConversionEngine):
    """Mock zero-shot voice conversion engine for high-speed automated unit testing."""

    @property
    def name(self) -> str:
        return "mock-voice-conversion"

    @property
    def supported_languages(self) -> List[str]:
        return ["en", "hi", "es"]

    def is_available(self) -> bool:
        return True

    def convert_voice(
        self,
        source_audio_path: Path,
        reference_audio_path: Path,
        output_path: Path,
        language: str = None,
        diffusion_steps: int = 25,
    ) -> float:
        """Simulate Speech-to-Speech conversion preserving source duration and applying target timbre."""
        if not source_audio_path or not Path(source_audio_path).exists():
            raise ValueError("Source audio recording file does not exist.")
        if not reference_audio_path or not Path(reference_audio_path).exists():
            raise ValueError("Target reference voice recording file does not exist.")

        sample_rate = 22050
        duration = 3.0

        # Attempt to read actual source duration
        try:
            import soundfile as sf
            info = sf.info(str(source_audio_path))
            duration = max(0.5, round(info.duration, 2))
        except Exception:
            duration = 3.0

        total_samples = int(sample_rate * duration)
        samples = []
        for i in range(total_samples):
            t = i / sample_rate
            # Simulated vocal waveform at target pitch (220Hz harmonic series)
            val = 0.4 * math.sin(2 * math.pi * 220 * t) + 0.2 * math.sin(2 * math.pi * 330 * t)
            pcm_val = max(-32767, min(32767, int(val * 16000)))
            samples.append(pcm_val)

        raw_pcm = struct.pack(f"<{len(samples)}h", *samples)
        num_channels = 1
        bytes_per_sample = 2
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        data_size = len(raw_pcm)

        header = (
            b"RIFF"
            + struct.pack("<I", 36 + data_size)
            + b"WAVE"
            + b"fmt "
            + struct.pack("<IHHIIHH", 16, 1, num_channels, sample_rate, byte_rate, block_align, 16)
            + b"data"
            + struct.pack("<I", data_size)
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        watermarked_bytes = stamp_wav_provenance(header + raw_pcm, model_name=self.name)
        output_path.write_bytes(watermarked_bytes)

        return duration

