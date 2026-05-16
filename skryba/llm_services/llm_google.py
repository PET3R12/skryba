import os
from typing import Dict
import google.generativeai as genai
from skryba.llm_services.baseLLM import BaseLLM


class GoogleLLM(BaseLLM):
    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(self, logger_instance=None):
        super().__init__(logger_instance)

        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GOOGLE_API_KEY in environment.")

        genai.configure(api_key=self.api_key)
        # Nie inicjalizujemy self.model tutaj, bo system_prompt
        # będzie się zmieniać przy każdym wywołaniu 'generate'
        # self.model = genai.GenerativeModel(self.DEFAULT_MODEL) # <-- USUNIĘTE

    def generate(self, context: Dict[str, str], prompt_template: Dict[str, str]) -> str:
        # Rozpakowujemy nową strukturę promptu
        system_prompt = prompt_template["system"]
        user_template = prompt_template["user_template"]

        # Formatujemy tylko szablon użytkownika
        full_prompt = user_template.format(**context)
        self.logger.info("Sending prompt to Google Gemini")

        try:
            # Tworzymy model *z* odpowiednim promptem systemowym
            # Jest to konieczne, ponieważ prompt systemowy jest dynamiczny
            model_with_system_prompt = genai.GenerativeModel(
                self.DEFAULT_MODEL, system_instruction=system_prompt
            )

            response = model_with_system_prompt.generate_content(full_prompt)
            return response.text if hasattr(response, "text") else str(response)
        except Exception as e:
            self.logger.error(f"Google Gemini error: {e}")
            raise
