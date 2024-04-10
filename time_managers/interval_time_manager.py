import asyncio
import pytz
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Tuple


from .time_manager import AbstractTimeManager
from ..enders import AbstractEnder
from ..element import Mode

class IntervalTimeManager(AbstractTimeManager, AbstractEnder):
    def __init__(self, interval : timedelta, offset : timedelta = None, simulation_start_date : datetime = None, simulation_end_date : datetime = None) -> None:
        self.interval = interval
        self.offset = offset if offset is not None else timedelta(0)
        self.simulation_start_date = simulation_start_date
        self.simulation_end_date = simulation_end_date


    async def reset(self, seed = None)->None:
        await super().reset(seed= seed)
        self.mode = self.get_trading_env().mode

        if self.mode.value == Mode.SIMULATION.value:
            self.__current_datetime = self.simulation_start_date
            
        elif self.mode.value == Mode.PRODUCTION.value:
            date = datetime.now(pytz.UTC)
            self.__current_datetime = floor_time(date, self.interval, self.offset)
            print(self.__current_datetime)
        
    async def get_current_datetime(self) -> datetime:
        return self.__current_datetime
    

    async def get_historical_datetime(self, step_back=0, relative_date : datetime = None) -> datetime:
        if relative_date is None: relative_date = await self.get_current_datetime() 
        if step_back < 0: raise ValueError("step_back must be positive")
        return relative_date - self.interval * step_back
    
    async def step(self):
        self.__current_datetime = await self.get_current_datetime() + self.interval
        
        if self.mode.value == Mode.PRODUCTION.value:
            delay = (self.__current_datetime - datetime.now(pytz.UTC)).total_seconds()
            print(f"Waiting {delay:0.2f} sec...")
            await asyncio.sleep(delay= delay)

    async def check(self) -> Tuple[bool, bool]:
        trainable = True
        terminated = False
        truncated = False

        if self.mode.value == Mode.SIMULATION.value:
            if await self.get_current_datetime() >= self.simulation_end_date:
                truncated = True

        return terminated, truncated, trainable



        


def floor_time(date : datetime, time_delta : timedelta, offset : timedelta):
   epoch = datetime(1970, 1, 1, tzinfo=pytz.UTC)
   return date - (date - offset - epoch) % time_delta