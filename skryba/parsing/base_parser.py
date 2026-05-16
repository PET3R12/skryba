from abc import ABC, abstractmethod
from structlog.typing import FilteringBoundLogger


class BaseParser(ABC):
    def __init__(self, logger_instance: FilteringBoundLogger = None) -> None:
        self.logger = logger_instance

    @abstractmethod
    def parse(self, *args, **kwargs) -> any:
        """Implement in subclass to perform parsing logic."""
        pass
