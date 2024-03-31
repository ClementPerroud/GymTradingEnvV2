from abc import ABC, abstractmethod
import gymnasium as gym
from datetime import datetime
import uuid
from typing import List

from ..time_managers import AbstractTimeManager
from ..exchanges import AbstractExchange
from ..observers import AbstractObserver
from ..enders import AbstractEnder, CompositeEnder, ender_deep_search
from ..element import AbstractEnvironmentElement, element_deep_search

class AbstractTradingEnv(gym.Env, CompositeEnder, ABC):
    instances = {}
    def __init__(self, time_manager : AbstractTimeManager, exchange_manager : AbstractExchange, enders : List[AbstractEnder]):
        self.time_manager = time_manager
        self.exchange_manager = exchange_manager

        self.initial_enders = enders

        super().__init__()

    @abstractmethod
    async def reset(self, date : datetime, seed = None):
        ...

    async def __reset__(self, date : datetime, seed = None):
        self.enders = ender_deep_search(self) + self.initial_enders

        self.env_elements : List[AbstractEnvironmentElement] = element_deep_search(self, excluded= [self.time_manager])
        self.env_elements.insert(0, self.time_manager) # Making sur time_manager is first of the reset list

        # Prepare for reset
        warm_steps_needed = 0
        for element in self.env_elements:
            element.set_trading_env(self)
            warm_steps_needed = max(warm_steps_needed, element.simulation_warmup_steps)
        
        # Reset all environment elements.
        for element in self.env_elements:
            await element.__reset__(date= date, seed = seed)
        # Go though the step needed for the environment to work
        for _ in range(warm_steps_needed + 1):
            await self.__step__()
            terminated, truncated = await self.check()
            if terminated or truncated: raise ValueError("Your environment has been terminated or truncated during initialization.")


    @abstractmethod
    async def step(self, date : datetime, seed = None):
        ...

    async def __step__(self):
        await self.time_manager.step()
        current_date = await self.time_manager.get_current_datetime()

        for element in self.env_elements:
            await element.__forward__(date= current_date)