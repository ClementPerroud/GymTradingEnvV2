from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from simulations import AbstractPairSimulation

from .time_manager import AbstractTimeManager
from enders import AbstractEnder

class SimulationTimeManager(AbstractTimeManager):

    def __init__(self, interval : timedelta | relativedelta) -> None:
        super().__init__()
        self.interval = interval
        self.__simulations : list[AbstractPairSimulation] = []

    def add_simulation(self, simulation : AbstractPairSimulation):
        self.__simulations.append(simulation)

    async def reset(self, date : datetime):
        self.__current_datetime = date
        self.__historic_datetimes : list[datetime] = [self.__current_datetime]
        for simultation in self.__simulations:
            simultation.reset(date = self.__current_datetime)

    async def get_current_datetime(self) -> datetime:
        return self.__current_datetime
    

    async def get_historical_datetime(self, step_back=0) -> datetime:
        if step_back < 0: raise ValueError("step_back must be positive")
        if step_back == 0: return await self.get_current_datetime()
        return self.__historic_datetimes[ - step_back - 1]
    

    async def step(self):
        await self.forward(date = await self.get_current_datetime() + self.interval)


    async def forward(self, date : datetime):
        for simultation in self.__simulations:
            simultation.forward(date= date)
        self.__current_datetime = date
        self.__historic_datetimes.append(self.__current_datetime)
        




        


