from abc import abstractmethod, ABC

class AbstractAction(ABC):
    @abstractmethod
    async def execute(self) -> None:
        ...
