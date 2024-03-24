from abc import ABC, abstractmethod
from datetime import datetime
from ..element import AbstractEnvironmentElement

class AbstractTimeManager(AbstractEnvironmentElement, ABC):
    @abstractmethod
    async def get_historical_datetime(self, step_back = 0, relative_date : datetime = None) -> datetime:
        ...

    @abstractmethod
    async def get_current_datetime(self) -> datetime:
        ...

    @abstractmethod
    async def reset(self, date : datetime, seed = None) -> None:
        ...

    @abstractmethod
    async def step(self):
        ...

