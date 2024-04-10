from abc import ABC, abstractmethod
from datetime import datetime

from ..element import AbstractEnvironmentElement
class AbstractReward(AbstractEnvironmentElement, ABC):
    def __init__(self, multiply_by = 1) -> None:
        self.multiply_by = multiply_by
        super().__init__()
    
    @abstractmethod
    async def reset(self, seed = None) -> None:
        ...
    
    @abstractmethod
    async def compute_reward(self):
        ...

    async def get(self) -> float:
        return self.multiply_by * await self.compute_reward()