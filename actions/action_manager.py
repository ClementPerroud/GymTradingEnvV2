
from abc import abstractmethod, ABC
from typing import TypeVar
from gymnasium.spaces import Space
from datetime import datetime

from ..element import AbstractEnvironmentElement
from ..utils.speed_analyser import astep_timer

ActType = TypeVar("ActType")

class AbstractActionManager(AbstractEnvironmentElement, ABC):
    def __init__(self) -> None:
        super().__init__()
        self.action_history = {}

    @astep_timer(step_name="Execute")
    async def __execute__(self, action : ActType, **kwargs) -> None:
        return await self.execute(action= action)

    async def reset(self, seed = None):
        self.time_manager = self.get_trading_env().time_manager

    async def get_action(self, date : datetime = None):
        if date == None : date = await self.time_manager.get_current_datetime()
        if date not in self.action_history:
            raise ValueError("date not found in action history.")
        return self.action_history[date]


    @abstractmethod
    async def execute(self, action : ActType) -> None:
        self.action_history[await self.time_manager.get_current_datetime()] = action

    @abstractmethod
    def action_space(self) -> Space:
        pass

