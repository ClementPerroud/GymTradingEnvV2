from abc import ABC, abstractmethod
import gymnasium as gym
from datetime import datetime
import numpy as np
from typing import List

from ..time_managers import AbstractTimeManager
from ..exchanges import AbstractExchange
from ..renderers import AbstractRenderer
from ..managers import PortfolioManager
from ..checkers import AbstractChecker, checker_deep_search
from ..element import AbstractEnvironmentElement, element_deep_search, Mode
from ..infos_manager import InfosManager


class AbstractTradingEnv(gym.Env, AbstractChecker, AbstractEnvironmentElement, ABC):
    instances = {}
    def __init__(self, name : str, mode : Mode, time_manager : AbstractTimeManager, exchange_manager : AbstractExchange, checkers : List[AbstractChecker], infos_manager : InfosManager, renderers : List[AbstractRenderer]) -> None:
        self.name = name
        self.mode = mode
        self.time_manager = time_manager
        self.exchange_manager = exchange_manager
        self.portfolio_manager = PortfolioManager()

        self.initial_checkers = checkers
        self.infos_manager = infos_manager
        self.renderers = renderers

        super().__init__()
        
    
    def _prepare_environment_elements(self):
        # Get all the environment elements
        self.env_elements : list[AbstractEnvironmentElement] = element_deep_search(self, excluded_classes= (AbstractTradingEnv,))
        self.env_elements.remove(self)
        
        # Sort the environment elements by order_index
        order_indexes = np.argsort([elem.order_index for elem in self.env_elements])
        self.env_elements = [self.env_elements[i] for i in order_indexes]

        for element in self.env_elements:
            element.set_trading_env(self)
        self.set_trading_env(self)
        
        checkers = checker_deep_search(self.env_elements) + self.initial_checkers
        self.checkers = list(dict.fromkeys(checkers)) # Exclude doublons

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
                terminated, truncated, trainable = await self.__check__()
                if terminated or truncated:
                    if _try >= 3: raise ValueError("Your environment has been terminated or truncated during initialization too many times.")
                    print(f"Warning : The environment initialization failed. Retry {_try + 1} ...")
                    return await self.__reset__(seed = seed, _try = _try + 1) 
        return trainable



    @abstractmethod
    async def step(self, date : datetime, seed = None):
        ...

    async def __step__(self):
        # Perform a step in the environment
        await self.time_manager.step()
        current_date = await self.time_manager.get_current_datetime()
        for element in self.env_elements:
            await element.__forward__(date= current_date)


    async def __check__(self):
        terminated, truncated, trainable = False, False, True
        checker_tasks = []

        for checker in self.checkers:
            if id(checker) is not id(self): # To avoid recursive call which would lead to an infinite loop
                checker_tasks.append(checker.check())
        checker_results = await self.gather(*checker_tasks)

        for checker_result in checker_results:
            checker_terminated, checker_truncated, checker_trainable = checker_result
            terminated, truncated, trainable = (terminated or checker_terminated), (truncated or checker_truncated), (trainable and checker_trainable)
        
        return terminated, truncated, trainable

    async def __render__(self, action, obs, reward, terminated, truncated, infos, **kwargs):
        render_steps, render_episode = [], []
        for renderer in self.renderers: 
            render_steps.append(renderer.render_step(action, obs, reward, terminated, truncated, infos))
            if terminated or truncated:
                render_episode.append(renderer.render_episode())
        # First : steps
        await self.gather(*render_steps)
        
        # Secondly : episode 
        await self.gather(*render_episode)