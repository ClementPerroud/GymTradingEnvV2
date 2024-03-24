from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from ..simulations import AbstractPairSimulation
from .time_manager import AbstractTimeManager


class SimulationTimeManager(AbstractTimeManager, ABC):
    def __init__(self) -> None:
        super().__init__()

    def add_simulation(self, simulation : AbstractPairSimulation):
        self.__simulations.append(simulation)

    @abstractmethod
    async def reset(self, date : datetime, seed = None)->None:
        self.__simulations : list[AbstractPairSimulation] = []
    
    @abstractmethod
    async def forward(self, date : datetime):
        for simultation in self.__simulations:
            await simultation.forward(date= date)
        



class IntervalSimulationTimeManager(SimulationTimeManager):
    def __init__(self, interval : timedelta | relativedelta) -> None:
        super().__init__()
        self.interval = interval

    async def reset(self, date : datetime, seed = None)->None:
        await super().reset(date= date, seed= seed)
        self.__current_datetime = date
        

    async def get_current_datetime(self) -> datetime:
        return self.__current_datetime
    

    async def get_historical_datetime(self, step_back=0, relative_date : datetime = None) -> datetime:
        if relative_date is None: relative_date = await self.get_current_datetime() 
        if step_back < 0: raise ValueError("step_back must be positive")
        return relative_date - self.interval * step_back
    

    async def step(self):
        await self.forward(date = await self.get_current_datetime() + self.interval)


    async def forward(self, date : datetime):
        await super().forward(date= date)
        self.__current_datetime = date
        




        


