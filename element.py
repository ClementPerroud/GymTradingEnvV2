from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, TYPE_CHECKING
from enum import Enum
import asyncio

from .utils.class_searcher import class_deep_search
from .utils.speed_analyser import astep_timer

if TYPE_CHECKING:
    from .environments import AbstractTradingEnv

class Mode(Enum):
    SIMULATION = 0
    PRODUCTION = 1

class AbstractEnvironmentElement(ABC):
    def __init__(self) -> None:
        super().__init__()
        self.__trading_env = None
    
    @property
    def simulation_warmup_steps(self) -> int:
        return 0

    def set_trading_env(self, trading_env):
        self.__trading_env = trading_env


    def get_trading_env(self) -> "AbstractTradingEnv":
        if self.__trading_env is None:
            ValueError("""
            Please provide the related trading_env during 
            initialization using the method .set_trading_env()
            This is usually not necessary when the instance is directly
            or indirectly linked to the trading environment, as 
            it is automatically set up.
            """)
        return self.__trading_env

    @property
    def order_index(self):
        return 0

    @astep_timer(step_name="Reset")
    async def __reset__(self, seed = None, **kwargs):
        return await self.reset(seed= seed)
    
    async def reset(self, seed = None):
        pass

    @astep_timer(step_name="Forward")
    async def __forward__(self, date : datetime, seed = None, **kwargs):
        return await self.forward(date= date, seed= seed)
    
    async def forward(self, date : datetime, seed = None):
        pass

    # Utils
    async def gather(self, *tasks):
        if self.get_trading_env().mode == Mode.PRODUCTION:
            return await asyncio.gather(*tasks)
        else:
            return [await task for task in tasks]
        return self.__class__.__name__


def element_deep_search(element,  excluded_classes = []) -> List[AbstractEnvironmentElement]:
    return list(class_deep_search(
        condition = lambda elem : isinstance(elem, AbstractEnvironmentElement),
        element= element
    ))