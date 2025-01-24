from gymnasium.spaces import Space, Box
import numpy as np
import asyncio
from datetime import datetime
from typing import List

from ..managers import PortfolioManager
from ..core import Pair, PortfolioExposition, Portfolio

from .observer import AbstractObserver

class ArrayConcatenateObserver(AbstractObserver):
    def __init__(self, sub_observers : List[AbstractObserver], axis = 0) -> None:
        super().__init__()
        self.sub_observers : List[AbstractObserver]= sub_observers
        if len(self.sub_observers) < 2 : raise ValueError("You must provide at least 2 sub-observers.")
        self.axis = 0

    
    @property
    def simulation_warmup_steps(self):
        return max([observer.simulation_warmup_steps for observer in self.sub_observers])
            

    def observation_space(self) -> Space:
        global_space = None
        for observer in self.sub_observers:
            if global_space is None: global_space = observer.observation_space()
            else:
                sub_space = observer.observation_space()
                if type(sub_space) is not type(global_space): raise TypeError(f"All the sub oservers must have the same type of Gymnasium Spaces.")

                if isinstance(global_space, Box):
                    sub_space : Box
                    global_shape = list(global_space.shape)
                    sub_shape = list(sub_space.shape)

                    if len(global_shape) != len(sub_shape):
                        raise TypeError("Invalid shapes")
                    
                    for index, x in enumerate(global_shape):
                        if index == self.axis:
                            global_shape[self.axis] += sub_shape[self.axis]
                        else:
                            if global_shape[index] != sub_shape[index]:
                                raise TypeError("Invalid shapes")
                    return Box(low= -np.inf, high= np.inf, shape= global_shape)

                else:
                    raise TypeError(f"Space {sub_space.__class__.__name__} not handled. Please consider using Box spaces.")
    
    async def get_obs(self, date : datetime = None):
        tasks = []
        
        for sub_observer in self.sub_observers:
            tasks.append(sub_observer.__get_obs__(date = date))
        results = await self.gather(*tasks)
        
        for i in range(len(results)):
            results[i] = np.array(results[i])
        return np.concatenate(results, axis = self.axis)
    
