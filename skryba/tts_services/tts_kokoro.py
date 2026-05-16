import structlog
from kokoro import KPipeline
import soundfile as sf
from pathlib import Path
import numpy as np
from skryba.tts_services.baseTTS import BaseTTS


class KokoroTTS(BaseTTS):
    def __init__(
        self, lang_code: str = "b", voice: str = "bm_daniel", logger_instance=None
    ):
        super().__init__(logger_instance or structlog.get_logger())
        self.lang_code = lang_code
        self.voice = voice
        self.pipeline = KPipeline(
            lang_code=self.lang_code, repo_id="hexgrad/Kokoro-82M"
        )

    def get_audio(
        self, text: str, output_path: Path = Path("output_kokoro.mp3")
    ) -> bytes:
        self.logger.info(
            "Generating audio with Kokoro TTS",
            voice=self.voice,
            lang_code=self.lang_code,
        )
        try:
            generator = self.pipeline(text, voice=self.voice)
            audio_fragments = []

            for i, (gs, ps, audio) in enumerate(generator):
                self.logger.debug("Appending audio fragment", index=i)
                audio_fragments.append(audio)

            full_audio = np.concatenate(audio_fragments)

            sf.write(output_path, full_audio, 24000)

            with open(output_path, "rb") as f:
                audio_data = f.read()

            self.logger.info("Audio saved", path=str(output_path))
            return audio_data
        except Exception as e:
            self.logger.error("Error generating audio", error=str(e))
            raise
