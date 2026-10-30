"""Abstract base class and protocol for voice synthesis engines."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class VoiceSynthesisEngine(ABC):
    """Abstract interface for local voice cloning engines."""

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
