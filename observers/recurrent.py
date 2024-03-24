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
        self.memory = [None for _ in range(self.window)]
    
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

    async def get_obs(self) -> list:
        # Update
        new_obs = await self.sub_observer.get_obs()
        self.memory.append(new_obs)
        self.memory.pop(0)

        # Check for missing values
        self.memory = await self.__fill_missing_historical_values(obs_list= self.memory)
        return np.array(self.memory, dtype= float)
        
    async def get_obs_at_date(self, date : datetime) -> list:
        obs_list = [None for _ in range(self.window)]
        return self.__fill_missing_historical_values(obs_list= obs_list, relative_date= date)

    async def __fill_missing_historical_values(self, obs_list :list, relative_date : datetime = None) -> list:
        # Check for missing values

        index_tasks = []
        async with asyncio.TaskGroup() as tg:
            for index, item in enumerate(obs_list): # Reverse the list to make step_back and index match
                if item is None:
                    obs_date = await self.time_manager.get_historical_datetime(step_back=self.window - 1 - index, relative_date= relative_date)
                    obs_list[index] = tg.create_task(self.sub_observer.get_obs_at_date(date= obs_date))
                    index_tasks.append(index)

        for index in index_tasks:
            obs_list[index] = obs_list[index].result()
        return obs_list

