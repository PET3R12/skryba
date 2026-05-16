from typing import Optional
import structlog
import os
from pathlib import Path
from dotenv import load_dotenv
import warnings
from elevenlabs.core import ApiError

from skryba.tts_services.tts_eleven_labs import ElevenLabsTTS
from skryba.tts_services.tts_google import GoogleTTS
from skryba.tts_services.tts_kokoro import KokoroTTS

load_dotenv()

warnings.filterwarnings(
    "ignore", message="dropout option adds dropout after all but last recurrent layer.*"
)
warnings.filterwarnings(
    "ignore", category=FutureWarning, message=".*torch.nn.utils.weight_norm.*"
)


class TTSPipeline:
    def __init__(
        self,
        text: str,
        lang: str,
        output_path: Path = Path("output/output_pipeline.mp3"),
        logger=None,
        tts_type: Optional[str] = None,
    ):
        self.text = text
        self.lang = lang.lower()
        self.output_path = Path(output_path)
        self.logger = logger or structlog.get_logger()
        self.tts_type = tts_type.lower() if tts_type else None

        self.has_elevenlabs_token = bool(os.getenv("TTS_API_KEY"))
        self.logger.info(
            "TTS_API_KEY found"
            if self.has_elevenlabs_token
            else "TTS_API_KEY not found"
        )

        self.elevenlabs = (
            ElevenLabsTTS(
                voice_id="TX3LPaxmHKxFdv7VOQHJ",
                model_id="eleven_multilingual_v2",
                logger_instance=self.logger,
            )
            if self.has_elevenlabs_token
            else None
        )

        self.gtts = GoogleTTS(lang="pl", logger_instance=self.logger)
        self.kokoro = KokoroTTS(
            lang_code="b", voice="bm_daniel", logger_instance=self.logger
        )

    def run(self) -> bytes:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.tts_type:
            self.logger.info("Forced TTS type specified", tts_type=self.tts_type)
            try:
                if self.tts_type == "elevenlabs":
                    if not self.elevenlabs:
                        raise RuntimeError(
                            "ElevenLabs is not available (missing TTS_API_KEY)"
                        )
                    return self.elevenlabs.get_audio(self.text, self.output_path)
                elif self.tts_type == "gtts":
                    return self.gtts.get_audio(self.text, self.output_path)
                elif self.tts_type == "kokoro":
                    return self.kokoro.get_audio(self.text, self.output_path)
                else:
                    raise ValueError(f"Unsupported tts_type: {self.tts_type}")
            except RuntimeError as re:
                self.logger.error("RuntimeError in TTS forced mode", error=str(re))
                if self.lang == "pl":
                    self.logger.info("Fallback to gTTS due to missing ElevenLabs token")
                    return self.gtts.get_audio(self.text, self.output_path)
                else:
                    self.logger.info(
                        "Fallback to Kokoro due to missing ElevenLabs token"
                    )
                    return self.kokoro.get_audio(self.text, self.output_path)
            except Exception as e:
                if self._is_invalid_api_key_exception(e):
                    self.logger.warning(
                        "Invalid ElevenLabs API key — switching to gTTS"
                    )
                    return self.gtts.get_audio(self.text, self.output_path)
                else:
                    raise

        if self.lang == "en":
            self.logger.info("Language is EN — using KokoroTTS")
            return self.kokoro.get_audio(self.text, self.output_path)

        elif self.lang == "pl":
            self.logger.info("Language is PL — trying ElevenLabs first")

            if self.elevenlabs:
                try:
                    return self.elevenlabs.get_audio(self.text, self.output_path)
                except Exception as e:
                    if self._is_token_limit_exception(e):
                        self.logger.warning(
                            "ElevenLabs token limit reached — switching to gTTS"
                        )
                        return self.gtts.get_audio(self.text, self.output_path)
                    elif self._is_invalid_api_key_exception(e):
                        self.logger.warning(
                            "Invalid ElevenLabs API key — switching to gTTS"
                        )
                        return self.gtts.get_audio(self.text, self.output_path)
                    else:
                        self.logger.error(
                            "ElevenLabs failed for another reason", error=str(e)
                        )
                        raise
            else:
                self.logger.info("Skipping ElevenLabs — using gTTS")
                return self.gtts.get_audio(self.text, self.output_path)

        else:
            self.logger.error("Unsupported language", lang=self.lang)
            raise ValueError(f"Unsupported language: {self.lang}")

    @staticmethod
    def _is_token_limit_exception(e: Exception) -> bool:
        if isinstance(e, ApiError):
            return e.body.get("detail", {}).get("status") == "quota_exceeded"
        return False

    @staticmethod
    def _is_invalid_api_key_exception(e: Exception) -> bool:
        if isinstance(e, ApiError):
            return e.body.get("detail", {}).get("status") == "invalid_api_key"
        return False


def main():
    text_en = "Solar Panel Detector is an AI-based project that aims to automatically recognize solar \n\npanels in satellite images. The tool can be used in monitoring energy infrastructure or spatial planning, among other things. The project demonstrates the ability to work with modern computer vision and data analysis technologies."
    text_pl = "Solar Panel Detector to projekt oparty na sztucznej inteligencji, którego celem jest automatyczne rozpoznawanie paneli słonecznych na zdjęciach satelitarnych. Narzędzie może znaleźć zastosowanie m.in. w monitorowaniu infrastruktury energetycznej czy planowaniu przestrzennym. Projekt pokazuje umiejętność pracy z nowoczesnymi technologiami wizji komputerowej i analizy danych."

    pipeline_en = TTSPipeline(
        text=text_en, lang="en", output_path=Path("output/eng.mp3")
    )
    pipeline_en.run()

    pipeline_pl = TTSPipeline(
        text=text_pl, lang="pl", output_path=Path("output/pl.mp3")
    )
    pipeline_pl.run()


if __name__ == "__main__":
    main()
