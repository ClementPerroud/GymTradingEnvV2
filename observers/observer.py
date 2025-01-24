import numpy as np
from datetime import datetime, timedelta
from abc import ABC, abstractmethod, abstractproperty
from gymnasium.spaces import Space

from ..element import AbstractEnvironmentElement
from ..utils.speed_analyser import astep_timer

class AbstractObserver(AbstractEnvironmentElement, ABC):
    @astep_timer(step_name="Get Obs")
    async def __get_obs__(self, date : datetime = None, **kwargs) -> np.ndarray:
        return await self.get_obs(date= date)



    @abstractmethod
    async def get_obs(self, date : datetime = None) -> np.ndarray:
        pass

    @abstractmethod
    def observation_space(self) -> Space:
        ...

