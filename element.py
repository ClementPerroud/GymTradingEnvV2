from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from .utils.class_searcher import class_deep_search
from . import environments

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


    def get_trading_env(self) -> "environments.RLTradingEnv":
        if self.__trading_env is None:
            ValueError("""
            Please provide the related trading_env during 
            initialization using the method .set_trading_env()
            This is usually not necessary when the instance is directly
            or indirectly linked to the trading environment, as 
            it is automatically set up.
            """)
        return self.__trading_env


    async def __reset__(self, date : datetime, seed = None):
        return await self.reset(date= date, seed= seed)
    
    async def reset(self, date : datetime, seed = None):
        pass

    async def __forward__(self, date : datetime, seed = None):
        return await self.forward(date= date, seed= seed)
    
    async def forward(self, date : datetime, seed = None):
        pass

def element_deep_search(element, excluded = []) -> List[AbstractEnvironmentElement]:
    return class_deep_search(
        condition = lambda element : isinstance(element, AbstractEnvironmentElement),
        element= element,
        list_to_fill= [],
        visited= [],
        excluded = excluded + [element]
    )