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

    async def get_obs(self, date : datetime = None) -> list:
        if date is None: date = await self.time_manager.get_current_datetime()

        tasks = []
        new_memory = {}
        steps_back = list(range(self.window))[::-1] 
        obs_dates = []
        async with asyncio.TaskGroup() as tg:
            for index in steps_back:
                obs_date = await self.time_manager.get_historical_datetime(step_back=index, relative_date= date)
                obs_dates.append(obs_date)
                if obs_date not in self.memory:
                    new_memory[obs_date] = tg.create_task(self.sub_observer.get_obs(date= obs_date))
                
        
        for obs_date in new_memory.keys():
            new_memory[obs_date] = new_memory[obs_date].result()
        self.memory.update(new_memory)
        
        results = [self.memory[obs_date] for obs_date in obs_dates]
        
        # Clean-up memory:
        if len(self.memory) >= self.window * 4:
            # Getting from size : self.window * 4 to self.windows * 3 by removing oldest elements
            for i in range(len(self.memory)):
                del self.memory[(next(iter(self.memory)))] # As dict are ordered by ascending order of the create datetime. This remove this oldest element

        return results # Reverse order in order to have the list ordered in ascending order on dates

