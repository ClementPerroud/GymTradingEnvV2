import numpy as np
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from gymnasium.spaces import Space,Box

from ..time_managers import AbstractTimeManager
from .observer import AbstractObserver

class RecurrentObserver(AbstractObserver):
    def __init__(self, sub_observer : AbstractObserver, window : int) -> None:
        super().__init__()
        self.sub_observer = sub_observer
        self.window = window

        
    async def reset(self, date : datetime, seed = None) -> None:
        self.time_manager = self.get_trading_env().time_manager
        self.memory = {}
    
    @property
    def simulation_warmup_steps(self):
        return self.sub_observer.simulation_warmup_steps + self.window
    
    def observation_space(self) -> Space:
        # Auto determination of the observation_space
        sub_observer_observation_space=  self.sub_observer.observation_space()
        if isinstance(sub_observer_observation_space, Box):
            shape = list(sub_observer_observation_space.shape)[:]
            shape.insert(0, self.window)
            return Box(shape = shape, low= -np.inf, high = np.inf)
        return NotImplemented

    def __clean_memory(self):
        if len(self.memory) >= self.window * 4:
            # Getting from size : self.window * 4 to self.windows * 3 by removing oldest elements
            for i in range(len(self.memory)):
                del self.memory[(next(iter(self.memory)))] # As dict are ordered by ascending order of the create datetime. This remove this oldest element

    async def get_obs(self, date : datetime = None) -> list:
        if date is None: date = await self.time_manager.get_current_datetime()

        new_memory = {}

        steps_back = list(range(self.window))[::-1] 
        window_date_tasks = []
        for index in steps_back:
            window_date_tasks.append(
                self.time_manager.get_historical_datetime(step_back=index, relative_date= date)
            )
        window_dates = await asyncio.gather(*window_date_tasks)

        update_memory_at_dates, new_obs_tasks = [], []
        for window_date in window_dates:
            if window_date not in self.memory:
                update_memory_at_dates.append(window_date)
                new_obs_tasks.append(self.sub_observer.get_obs(date= window_date))
        new_obs = await asyncio.gather(*new_obs_tasks)
        new_memory = dict(zip(update_memory_at_dates, new_obs))
        self.memory.update(new_memory)
        
        results = [self.memory[window_date] for window_date in window_dates]
        
        self.__clean_memory()
        return np.array(results) # Reverse order in order to have the list ordered in ascending order on dates

