import numpy as np
from abc import ABC, abstractmethod
from gymnasium.spaces import Space

class AbstractObserver(ABC):
    @abstractmethod
    async def get_obs(self) -> np.ndarray:
        pass

    @abstractmethod
    def observation_space(self) -> Space:
        ...
    
    @property
    @abstractmethod
    def observation_lookback(self) -> int:
        ...

    
