from abc import ABC, abstractmethod


class TextToSpeechService(ABC):
    """Provider-agnostic interface for converting text into speech audio.

    A future phase will plug in a concrete provider (e.g. a cloud TTS API)
    without requiring changes to the AI advisor or calculation engines.
    """

    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """Synthesize speech audio bytes from text."""
