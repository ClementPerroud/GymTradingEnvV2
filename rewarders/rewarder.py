from abc import ABC, abstractmethod
from datetime import datetime

from ..element import AbstractEnvironmentElement
from ..utils.speed_analyser import astep_timer

class AbstractRewarder(AbstractEnvironmentElement, ABC):
    def __init__(self, multiply_by = 1) -> None:
        self.multiply_by = multiply_by
        super().__init__()
    
    @abstractmethod
    async def reset(self, seed = None) -> None:
        ...
    
    @abstractmethod
    async def compute_reward(self):
        ...

    @astep_timer("Reward")
    async def __get__(self, **kwargs) -> float:
        return await self.get()
    
    async def get(self) -> float:
        return self.multiply_by * await self.compute_reward()

