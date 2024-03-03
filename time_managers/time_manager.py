from abc import ABC, abstractmethod
from datetime import datetime


class AbstractTimeManager(ABC):
    @abstractmethod
    async def get_historical_datetime(self, back = 0) -> datetime:
        ...

    @abstractmethod
    async def get_current_datetime(self) -> datetime:
        ...

    @abstractmethod
    async def reset(self, date : datetime) -> None:
        ...

    @abstractmethod
    async def step(self):
        ...

