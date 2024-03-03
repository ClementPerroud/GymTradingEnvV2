
from abc import abstractmethod, ABC
from typing import TypeVar
from gymnasium.spaces import Space
ActType = TypeVar("ActType")

class AbstractActionManager(ABC):
    @abstractmethod
    async def execute(self, action : ActType) -> None:
        pass

    @abstractmethod
    def action_space(self) -> Space:
        pass

