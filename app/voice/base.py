"""Abstract base class and protocol for voice synthesis engines."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional


class VoiceSynthesisEngine(ABC):
    """Abstract interface for local text-to-speech voice cloning engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return engine identification name."""
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """Return list of ISO language codes supported by this engine."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine dependencies and weights are installed locally."""
        pass

    @abstractmethod
    def synthesize(
        self,
        text: str,
        reference_audio_path: Path,
        output_path: Path,
        language: str = "es",
        speed: float = 1.0,
    ) -> float:
        """Synthesize text using reference audio voice, saving to output_path.

        Returns:
            Duration of synthesized audio in seconds.
        """
        pass


class VoiceConversionEngine(ABC):
    """Abstract interface for genuine Zero-Shot Speech-to-Speech Voice Conversion (Audio-to-Audio)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return engine identification name (e.g. 'seed-vc', 'mock-vc')."""
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """Return list of language codes with verified speech conversion fidelity."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine dependencies and weights are installed locally."""
        pass

    @abstractmethod
    def convert_voice(
        self,
        source_audio_path: Path,
        reference_audio_path: Path,
        output_path: Path,
        language: Optional[str] = None,
        diffusion_steps: int = 25,
    ) -> float:
        """Convert source microphone audio directly into target speaker's vocal characteristics.

        Preserves source words, pronunciation, prosody, and rhythm while applying the
        target speaker's vocal timbre.

        Args:
            source_audio_path: Path to user's recorded microphone audio (words to preserve).
            reference_audio_path: Path to target reference voice recording (timbre to clone).
            output_path: Path to write the converted speech WAV.
            language: Optional language hint (e.g. 'en', 'hi').
            diffusion_steps: Number of diffusion / flow-matching sampling steps.

        Returns:
            Duration of converted audio in seconds.
        """
        pass

