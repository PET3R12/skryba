import os
from typing import Dict
from langchain_openai import ChatOpenAI
from skryba.llm_services.baseLLM import BaseLLM
from langchain_core.messages import SystemMessage, HumanMessage  # <-- DODANE


class OpenRouterLLM(BaseLLM):
    DEFAULT_MODEL = "meta-llama/llama-4-maverick"

    def __init__(self, logger_instance=None):
        super().__init__(logger_instance)

        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("Missing OPENROUTER_API_KEY in environment.")

        self.model = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
            model=self.DEFAULT_MODEL,
            temperature=0.1,
        )

    def generate(self, context: Dict[str, str], prompt_template: Dict[str, str]) -> str:
        system_prompt = prompt_template["system"]
        user_template = prompt_template["user_template"]

        # Formatujemy tylko szablon użytkownika
        full_prompt = user_template.format(**context)
        self.logger.info("Sending prompt to OpenRouter")

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=full_prompt),
        ]

        try:
            response = self.model.invoke(messages)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            self.logger.error(f"OpenRouter error: {e}")
            raise
