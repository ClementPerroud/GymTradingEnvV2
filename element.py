from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, TYPE_CHECKING
from enum import Enum

from .utils.class_searcher import class_deep_search

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
        if self not in trading_env.env_elements: trading_env.env_elements.append(self)
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

    async def __reset__(self, seed = None):
        return await self.reset(seed= seed)
    
    async def reset(self, seed = None):
        pass

    async def __forward__(self, date : datetime, seed = None):
        return await self.forward(date= date, seed= seed)
    
    async def forward(self, date : datetime, seed = None):
        pass


def element_deep_search(element,  excluded_classes = []) -> List[AbstractEnvironmentElement]:
    return class_deep_search(
        condition = lambda elem : isinstance(elem, AbstractEnvironmentElement),
        element= element,
        list_to_fill= [],
        visited= [],
        excluded = [id(element)],
        excluded_classes = tuple(excluded_classes)
    )