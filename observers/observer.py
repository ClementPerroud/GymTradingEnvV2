import numpy as np
from datetime import datetime, timedelta
from abc import ABC, abstractmethod, abstractproperty
from gymnasium.spaces import Space

from ..element import AbstractEnvironmentElement
from ..utils.speed_analyser import astep_timer

class AbstractObserver(AbstractEnvironmentElement, ABC):
    def __init__(self, transform_function = None):
        self._transform_function = transform_function
        super().__init__()
    @astep_timer(step_name="Get Obs")
    async def __get_obs__(self, date : datetime = None, **kwargs) -> np.ndarray:
        return self.transform(await self.get_obs(date= date))


    @abstractmethod
    async def get_obs(self, date : datetime = None) -> np.ndarray:
        pass

    @abstractmethod
    def observation_space(self) -> Space:
        ...

    def transform(self, obs) -> np.ndarray:
        if self._transform_function is None: return obs
        else: return self._transform_function(obs) 
            
