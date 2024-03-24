from abc import ABC, abstractmethod
from datetime import datetime

from ..element import AbstractEnvironmentElement
class AbstractReward(AbstractEnvironmentElement, ABC):
    @property
    def multiply_by(self):
        return 1
    
    @abstractmethod
    async def reset(self, date : datetime, seed = None) -> None:
        ...
    
    @abstractmethod
    async def compute_reward(self):
        ...

    async def get(self) -> float:
        return self.multiply_by * await self.compute_reward()