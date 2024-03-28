import numpy as np
from datetime import datetime, timedelta
from abc import ABC, abstractmethod, abstractproperty
from gymnasium.spaces import Space

from ..element import AbstractEnvironmentElement

class AbstractObserver(AbstractEnvironmentElement, ABC):


    @abstractmethod
    async def get_obs(self, date : datetime = None) -> np.ndarray:
        pass

    @abstractmethod
    def observation_space(self) -> Space:
        ...

