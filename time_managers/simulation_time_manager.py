from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from simulations import AbstractPairSimulation

from .time_manager import AbstractTimeManager
from enders import AbstractEnder

class IntervalSimulationTimeManager(AbstractTimeManager):
    def __init__(self, interval : timedelta | relativedelta) -> None:
        super().__init__()
        self.interval = interval
        self.__simulations : list[AbstractPairSimulation] = []

    def add_simulation(self, simulation : AbstractPairSimulation):
        self.__simulations.append(simulation)

    async def reset(self, date : datetime):
        self.__current_datetime = date
        for simultation in self.__simulations:
            await simultation.reset(date = self.__current_datetime)

    async def get_current_datetime(self) -> datetime:
        return self.__current_datetime
    

    async def get_historical_datetime(self, step_back=0, relative_date : datetime = None) -> datetime:
        if relative_date is None: relative_date = await self.get_current_datetime() 
        if step_back < 0: raise ValueError("step_back must be positive")
        return relative_date - self.interval * step_back
    

    async def step(self):
        await self.forward(date = await self.get_current_datetime() + self.interval)


    async def forward(self, date : datetime):
        for simultation in self.__simulations:
            await simultation.forward(date= date)
        self.__current_datetime = date
        




        


