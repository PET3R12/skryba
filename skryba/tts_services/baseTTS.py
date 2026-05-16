from abc import abstractmethod, ABC
from structlog.typing import FilteringBoundLogger


class BaseTTS(ABC):
    def __init__(self, logger_instance: FilteringBoundLogger = None) -> None:
        self.logger = logger_instance

        @abstractmethod
        def get_audio(self, *args, **kwargs) -> any:
            """
            Abstract method to generate audio from text using a specified voice.
            """
            pass
