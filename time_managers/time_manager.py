from abc import ABC, abstractmethod
from datetime import datetime
from ..element import AbstractEnvironmentElement

class AbstractTimeManager(AbstractEnvironmentElement, ABC):
    @property
    def order_index(self):
        return -200
    
    @abstractmethod
    async def get_historical_datetime(self, step_back = 0, relative_date : datetime = None) -> datetime:
        ...

    @abstractmethod
    async def get_current_datetime(self) -> datetime:
        ...

    @abstractmethod
    async def step(self):
        ...

