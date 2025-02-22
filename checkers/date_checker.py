from datetime import datetime
from typing import Tuple

from .checker import AbstractChecker

class DateChecker(AbstractChecker):
    def __init__(self,
            end_date : datetime,
        ) -> None:
        self.end_date = end_date

    async def reset(self, seed = None):
        self.time_mangager = self.get_trading_env().time_manager

    
    async def check(self) -> Tuple[bool, bool, bool]:
        terminated, truncated, trainable = False, False, True


        if await self.time_mangager.get_current_datetime() >= self.end_date:
            truncated = True

        return terminated, truncated, trainable