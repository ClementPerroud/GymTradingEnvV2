from datetime import datetime
from typing import Tuple

from .ender import AbstractEnder

class DateEnder(AbstractEnder):
    def __init__(self,
            end_date : datetime,
        ) -> None:
        self.end_date = end_date

    async def reset(self, seed = None):
        self.time_mangager = self.get_trading_env().time_manager

    
    async def check(self) -> Tuple[bool, bool]:
        trainable = True
        terminated = False
        truncated = False

        if await self.time_mangager.get_current_datetime() >= self.end_date:
            truncated = True

        return terminated, truncated, trainable