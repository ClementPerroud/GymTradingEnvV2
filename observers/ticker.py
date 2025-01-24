from gymnasium.spaces import Space, Box
import numpy as np
from datetime import datetime
from typing import Dict

from ..exchanges.responses import TickerResponse
from ..core import Pair
from ..utils.async_lru import alru_cache

from .observer import AbstractObserver


class TickerObserver(AbstractObserver):
    def __init__(self, pair : Pair, mean_steps = 48) -> None:
        super().__init__()

        self.pair = pair

    async def reset(self, seed = None) -> None:
        # self.__lru_get_obs.cache_clear()
        
        self.time_manager = self.get_trading_env().time_manager
        self.exchange_manager = self.get_trading_env().exchange_manager
        self.previous_tickers : Dict[datetime, TickerResponse] = {}
    
    @property
    def simulation_warmup_steps(self):
        return 0

    def observation_space(self) -> Space:
        return Box(shape = (5,), high = np.inf, low = 0)

    async def get_obs(self, date : datetime = None):
        if date is None: date = await self.time_manager.get_current_datetime()
        ticker = await self.exchange_manager.get_ticker(pair = self.pair, date = date)
        return np.array([
            float(ticker.open.amount),
            float(ticker.high.amount),
            float(ticker.low.amount),
            float(ticker.close.amount),
            float(ticker.volume.amount)
        ])





