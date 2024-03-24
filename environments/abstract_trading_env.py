from abc import ABC, abstractmethod
import gymnasium as gym
from datetime import datetime
import uuid

from ..time_managers import AbstractTimeManager
from ..exchanges import AbstractExchange
from ..observers import AbstractObserver
from ..element import AbstractEnvironmentElement, element_deep_search

class AbstractTradingEnv(gym.Env, ABC):
    instances = {}
    def __init__(self, time_manager : AbstractTimeManager, exchange : AbstractExchange):
        self.time_manager = time_manager
        self.exchange = exchange

        super().__init__()
        self.id = uuid.uuid4().hex
        self.instances[self.id] = self

    async def reset(self, date : datetime, seed = None):
        self.env_elements : list[AbstractEnvironmentElement] = element_deep_search(self, excluded= [self.time_manager])
        self.env_elements.insert(0, self.time_manager) # Making sur time_manager is first of the reset list

        # Prepare for reset
        warm_steps_needed = 0
        for element in self.env_elements:
            element.set_trading_env(self)
            warm_steps_needed = max(warm_steps_needed, element.simulation_warmup_steps)
        
        # Reset all environment elements.
        for element in self.env_elements:
            await element.reset(date= date, seed = seed)

        # Go though the step needed for the environment to work
        for _ in range(warm_steps_needed + 1):
            await self.time_manager.step()
            terminated, truncated = await self.check()
            if terminated or truncated: raise ValueError("Your environment has been terminated or truncated during initialization.")
