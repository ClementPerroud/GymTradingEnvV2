from gymnasium.spaces import Space, Box
import numpy as np
from datetime import datetime, timedelta
import asyncio
from typing import List, Dict
from decimal import Decimal
from async_lru import alru_cache

from ..exchanges import AbstractExchange
from ..exchanges.responses import TickerResponse
from ..time_managers import AbstractTimeManager
from ..core import Pair

from .observer import AbstractObserver

class TickerObserver(AbstractObserver):
    def __init__(self, pair : Pair, mean_steps = 200) -> None:
        super().__init__()

        self.pair = pair
        self.mean_steps = mean_steps
        self.memory_size = self.simulation_warmup_steps + 10

    async def reset(self, date : datetime, seed = None) -> None:
        self.__lru_get_obs.cache_clear()
        
        self.time_manager = self.get_trading_env().time_manager
        self.exchange_manager = self.get_trading_env().exchange_manager
        self.previous_tickers : Dict[datetime, TickerResponse] = {}
    
    @property
    def simulation_warmup_steps(self):
        return self.mean_steps + 1

    def observation_space(self) -> Space:
        return Box(shape = (3,), high = np.inf, low = - np.inf)

    async def get_obs(self, date : datetime = None):
        if date is None: date = await self.time_manager.get_current_datetime()
        return await self.__lru_get_obs(date= date)
    
    @alru_cache(maxsize= 200)
    async def __lru_get_obs(self, date : datetime):

        tickers : List[TickerResponse]  = await asyncio.gather(
            *[self.exchange_manager.get_ticker(
                pair = self.pair, 
                date = await self.time_manager.get_historical_datetime(step_back=i, relative_date= date)
            )
                for i in range(self.mean_steps)
            ]
        )
        ticker = tickers[0]
        previous_ticker = tickers[1]
        high_feature = ticker.high / ticker.open - 1
        low_feature = ticker.low / ticker.open - 1
        close_feature = ticker.close / previous_ticker.close - 1

        volume_feature = (ticker.volume * Decimal(self.mean_steps)) / sum([t.volume for t in tickers[1:]], start = ticker.volume)
        result =  [
            float(high_feature), 
            float(low_feature), 
            float(close_feature),
            float(volume_feature)
        ]
        return np.array(result)
