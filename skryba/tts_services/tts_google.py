from gtts import gTTS
from skryba.tts_services.baseTTS import BaseTTS
import structlog
from pathlib import Path


class GoogleTTS(BaseTTS):
    def __init__(self, lang: str = "pl", logger_instance=None):
        super().__init__(logger_instance or structlog.get_logger())
        self.lang = lang

    def get_audio(self, text: str, output_path: Path = Path("output.mp3")) -> bytes:
        self.logger.info("Generating audio with gTTS", lang=self.lang)
        try:
            tts = gTTS(text=text, lang=self.lang)
            tts.save(str(output_path))
            self.logger.info("Saved gTTS audio", path=output_path)
            with open(output_path, "rb") as f:
                return f.read()
        except Exception as e:
            self.logger.error("gTTS generation failed", error=str(e))
            raise
