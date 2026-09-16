from abc import ABC, abstractmethod

from app.services.ai.ai_advisor_service import AIAdvisorService
from app.services.voice.speech_to_text_service import SpeechToTextService
from app.services.voice.text_to_speech_service import TextToSpeechService


class VoiceAdvisorService(ABC):
    """Orchestrates the future voice pipeline.

    User voice -> SpeechToTextService -> AIAdvisorService -> calculation
    engines -> AI explanation -> TextToSpeechService -> voice response.

    Depending on the interfaces rather than concrete providers keeps the voice
    pipeline swappable without touching the calculation engines.
    """

    def __init__(
        self,
        speech_to_text: SpeechToTextService,
        ai_advisor: AIAdvisorService,
        text_to_speech: TextToSpeechService,
    ) -> None:
        self.speech_to_text = speech_to_text
        self.ai_advisor = ai_advisor
        self.text_to_speech = text_to_speech

    @abstractmethod
    def handle_voice_query(self, audio_bytes: bytes) -> bytes:
        """Run the full voice pipeline and return a synthesized audio response."""
