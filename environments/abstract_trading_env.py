from abc import ABC, abstractmethod
import gymnasium as gym
from datetime import datetime
import numpy as np
from typing import List

from ..time_managers import AbstractTimeManager
from ..exchanges import AbstractExchange
from ..observers import AbstractObserver
from ..enders import AbstractEnder, CompositeEnder, ender_deep_search
from ..element import AbstractEnvironmentElement, element_deep_search, Mode


class AbstractTradingEnv(gym.Env, CompositeEnder, ABC):
    instances = {}
    def __init__(self, mode : Mode, time_manager : AbstractTimeManager, exchange_manager : AbstractExchange, enders : List[AbstractEnder]):
        self.mode = mode
        self.time_manager = time_manager
        self.exchange_manager = exchange_manager

        self.initial_enders = enders

        super().__init__()
        
    
    def _prepare_environment_elements(self):
        # Get all the environment elements
        self.env_elements : list[AbstractEnvironmentElement] = element_deep_search(self)
        self.env_elements.remove(self)
        
        # Sort the environment elements by order_index
        order_indexes = np.argsort([elem.order_index for elem in self.env_elements])
        self.env_elements = [self.env_elements[i] for i in order_indexes]

        for element in self.env_elements:
            element.set_trading_env(self)
        self.set_trading_env(self)

        enders = ender_deep_search(self.env_elements) + self.initial_enders
        self.enders = list(dict.fromkeys(enders)) # Exclude doublons

    @abstractmethod
    async def reset(self, seed = None):
        ...

    async def __reset__(self, seed = None, _try = 0):

        self._prepare_environment_elements()
        # Prepare the environment elements and retrieve the warmup steps needed
        warm_steps_needed = 0
        
        for element in self.env_elements:
            warm_steps_needed = max(warm_steps_needed, element.simulation_warmup_steps)
        
        # Reset all environment elements.
        for element in self.env_elements:
            await element.__reset__(seed = seed)
        
        # Go though the step needed for the environment to work
        if self.mode.value == Mode.SIMULATION.value:
            for i in range(warm_steps_needed + 1):
                await self.__step__()
                terminated, truncated = await self.__check__()
                if terminated or truncated:
                    if _try >= 3: raise ValueError("Your environment has been terminated or truncated during initialization too many times.")
                    print(f"Warning : The environment initialization failed. Retry {_try + 1} ...")
                    return await self.__reset__(seed = seed, _try = _try + 1) 



    @abstractmethod
    async def step(self, date : datetime, seed = None):
        ...

    async def __step__(self):
        # Perform a step in the environment
        await self.time_manager.step()
        current_date = await self.time_manager.get_current_datetime()
        for element in self.env_elements:
            await element.__forward__(date= current_date)

