from skryba.llm_services.baseLLM import BaseLLM
import os
import structlog
from typing import Dict

from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv, find_dotenv


class GroqLLM(BaseLLM):
    DEFAULT_MODEL = "llama-3.1-8b-instant"

    def __init__(self, logger_instance=None):
        super().__init__(logger_instance or structlog.get_logger())

        load_dotenv(find_dotenv(usecwd=True))

        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GROQ_API_KEY.")

        from langchain_groq import ChatGroq

        self.model = ChatGroq(
            model=self.DEFAULT_MODEL, temperature=0.1, api_key=self.api_key
        )

    def generate(self, context: Dict[str, str], prompt_template: Dict[str, str]) -> str:
        system_prompt = prompt_template["system"]
        user_template = prompt_template["user_template"]

        user_prompt = user_template.format(**context)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        self.logger.info("Sending prompt to Groq")
        try:
            response = self.model.invoke(messages)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            self.logger.error(f"Groq error: {e}")
            raise
