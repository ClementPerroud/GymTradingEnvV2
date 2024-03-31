from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List

from .time_manager import AbstractTimeManager




class IntervalSimulationTimeManager(AbstractTimeManager):
    def __init__(self, interval : timedelta) -> None:
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
        self.__current_datetime = await self.get_current_datetime() + self.interval

        




        


