from abc import ABC, abstractmethod

from ..element import AbstractEnvironmentElement
class AbstractReward(AbstractEnvironmentElement, ABC):
    @abstractmethod
    async def reset(self, date) -> None:
        ...
    
    @abstractmethod
    async def get(self) -> float:
        ...