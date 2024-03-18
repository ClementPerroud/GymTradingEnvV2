from abc import abstractmethod, ABC
from element import AbstractEnvironmentElement

class AbstractAction(ABC):
    @abstractmethod
    async def execute(self) -> None:
        ...
