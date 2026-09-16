from abc import ABC, abstractmethod


class SpeechToTextService(ABC):
    """Provider-agnostic interface for converting speech audio into text.

    A future phase will plug in a concrete provider (e.g. a cloud speech API)
    without requiring changes to the AI advisor or calculation engines.
    """

    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe raw audio bytes into text."""
