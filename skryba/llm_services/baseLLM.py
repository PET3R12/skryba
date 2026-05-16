from abc import ABC, abstractmethod
from typing import Dict
import structlog


class BaseLLM(ABC):
    def __init__(self, logger_instance=None):
        self.logger = logger_instance or structlog.get_logger()

    @abstractmethod
    def generate(self, context: Dict[str, str], prompt_template: Dict[str, str]) -> str:
        """
        Generate a response using the LLM based on given context and prompt structure.
        'prompt_template' is expected to be a dict with 'system' and 'user_template' keys.
        """
        pass
