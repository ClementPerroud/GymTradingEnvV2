from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from .utils.class_searcher import class_deep_search
from . import environments

class AbstractEnvironmentElement(ABC):
    def __init__(self) -> None:
        self.__reseted = False
        super().__init__()
    
    @property
    def simulation_warmup_steps(self) -> int:
        return 0

    def set_trading_env(self, trading_env):
        if self not in trading_env.env_elements: trading_env.env_elements.append(self)
        self.__trading_env = trading_env


    def get_trading_env(self) -> "environments.RLTradingEnv":
        return self.__trading_env

    async def reset(self, date : datetime, seed = None):
        pass


def element_deep_search(element, excluded = []) -> List[AbstractEnvironmentElement]:
    return class_deep_search(
        condition = lambda element : isinstance(element, AbstractEnvironmentElement),
        element= element,
        list_to_fill= [],
        visited= [],
        excluded = excluded + [element]
    )