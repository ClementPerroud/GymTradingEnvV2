from abc import abstractmethod, ABC
from typing import TypeVar

from ..element import AbstractEnvironmentElement

ActType = TypeVar("ActType")
class AbstractAction(AbstractEnvironmentElement, ABC):
    async def __execute__(self, action : ActType) -> None:
        if self.get_trading_env().speed_analyser.running: self.get_trading_env().speed_analyser.step("Execute " + self.__class__.__name__)
        result = await self.execute(action= action)
        if self.get_trading_env().speed_analyser.running: self.get_trading_env().speed_analyser.step("Unknown")
        return result

    @abstractmethod
    async def execute(self) -> None:
        ...
