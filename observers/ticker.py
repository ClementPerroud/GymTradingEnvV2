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
    def __init__(self, pair : Pair, mean_steps = 48) -> None:
        super().__init__()

        self.pair = pair
        self.mean_steps = mean_steps
        self.memory_size = self.simulation_warmup_steps + 10
        self.__scale = np.array([0.005, 0.005, 0.005, 0.005, 0.75])
    async def reset(self, date : datetime, seed = None) -> None:
        self.__lru_get_obs.cache_clear()
        
        self.time_manager = self.get_trading_env().time_manager
        self.exchange_manager = self.get_trading_env().exchange_manager
        self.previous_tickers : Dict[datetime, TickerResponse] = {}
    
    @property
    def simulation_warmup_steps(self):
        return self.mean_steps + 1

    def observation_space(self) -> Space:
        return Box(shape = (5,), high = np.inf, low = - np.inf)

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

        close_feature = float(ticker.close / previous_ticker.close) - 1
        open_feature = float(ticker.open / ticker.close) - 1
        high_feature = float(ticker.high / ticker.close) - 1
        low_feature = float(ticker.low / ticker.close) - 1
        volume_feature = float(ticker.volume.amount)  / (1E-3 + np.median([float(t.volume.amount) for t in tickers]))
        result =  np.array([
            float(close_feature),
            float(open_feature),
            float(high_feature), 
            float(low_feature), 
            float(volume_feature)
        ])
        return result / self.__scale
