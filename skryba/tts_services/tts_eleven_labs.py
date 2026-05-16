import structlog

import os
from dotenv import load_dotenv, find_dotenv
from elevenlabs.client import ElevenLabs
from skryba.tts_services.baseTTS import BaseTTS
from pathlib import Path


class ElevenLabsTTS(BaseTTS):
    def __init__(self, voice_id: str, model_id: str, logger_instance=None):
        super().__init__(logger_instance or structlog.get_logger())
        load_dotenv(find_dotenv(usecwd=True))
        self.api_key = os.getenv("TTS_API_KEY")
        if not self.api_key:
            raise ValueError("Missing TTS_API_KEY in environment.")
        self.voice_id = voice_id
        self.model_id = model_id
        self.client = ElevenLabs(api_key=self.api_key)

    def get_audio(self, text: str, output_path: Path = Path("output.mp3")) -> bytes:
        self.logger.info("Generating audio with ElevenLabs", voice_id=self.voice_id)
        try:
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.voice_id, model_id=self.model_id, text=text
            )
            audio_bytes = b"".join(audio_generator)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            self.logger.info("Saved ElevenLabs audio", path=output_path)
            return audio_bytes
        except Exception as e:
            self.logger.error("ElevenLabs generation failed", error=str(e))
            raise
