from abc import ABC, abstractmethod

class AbstractReward(ABC):
    @abstractmethod
    async def reset(self) -> None:
        ...
    
    @abstractmethod
    async def get(self) -> float:
        ...