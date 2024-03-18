import numpy as np
from datetime import datetime, timedelta
from abc import ABC, abstractmethod, abstractproperty
from gymnasium.spaces import Space
from element import AbstractEnvironmentElement

class AbstractObserver(AbstractEnvironmentElement, ABC):
    @abstractmethod
    async def get_obs_at_date(self, date : datetime) -> np.ndarray:
        pass

    @abstractmethod
    async def get_obs(self) -> np.ndarray:
        pass

    @abstractmethod
    def observation_space(self) -> Space:
        ...
    
    @abstractproperty
    def observation_lookback(self) -> int:
        ...

