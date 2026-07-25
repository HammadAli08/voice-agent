import os
import io
import logging
from groq import Groq
from src.core.config_manager import config

logger = logging.getLogger(__name__)

class STTEngine:
    def __init__(self):
        self.api_key = config.get("voice.groq_api_key")
        if not self.api_key:
            logger.error("Groq API key not found for STT.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "whisper-large-v3"

    def transcribe(self, audio_data):
        """
        Transcribes audio bytes to text using Groq Whisper.
        audio_data: Raw PCM audio bytes (should be converted to file-like object or appropriate format)
        """
        try:
            # Create WAV in memory
            from src.utils.audio_utils import create_wav_header
            wav_data = create_wav_header(audio_data)
            
            transcription = self.client.audio.transcriptions.create(
                file=("audio.wav", wav_data),
                model=self.model,
                response_format="json",
                language="en"
            )
            return transcription.text
        except Exception as e:
            logger.error(f"STT Error: {e}")
            return None
