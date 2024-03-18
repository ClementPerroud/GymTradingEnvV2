from abc import ABC, abstractmethod
from datetime import datetime
from element import AbstractEnvironmentElement

class AbstractPairSimulation(AbstractEnvironmentElement, ABC):
    def __init__(self, memory_size = 1000) -> None:
        super().__init__()
        self.memory_size = memory_size

    @abstractmethod
    async def reset(self, date : datetime) -> None:
        self.current_date = date
        self._data_memory = {}

    @abstractmethod
    async def forward(self, date : datetime) -> None:
        if date < self.current_date: raise ValueError(f"date must be ahead current date : {date < self.current_date}")
        self.current_date = date

    def get_data(self, date : datetime) -> dict:
        try:
            return self._data_memory[date]
        except KeyError as e:
            raise KeyError("Data not found.")

    def update_memory(self, date, data):
        if date in data: raise ValueError("Can not add to memory a data at an already existing date.")
        self._data_memory[date] = data
        if len(self._data_memory) > self.memory_size:
            del self._data_memory[next(iter(self._data_memory))]