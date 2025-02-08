from gymnasium.spaces import Space, Box, Dict
import numpy as np
from datetime import datetime

from ..exchanges.responses import TickerResponse
from ..core import Pair
from ..utils.async_lru import alru_cache

from .observer import AbstractObserver


class TickerObserver(AbstractObserver):
    def __init__(self, pair : Pair, **kwargs) -> None:
        super().__init__(**kwargs)

        self.pair = pair

    async def reset(self, seed = None) -> None:
        # self.__lru_get_obs.cache_clear()
        
        self.time_manager = self.get_trading_env().time_manager
        self.exchange_manager = self.get_trading_env().exchange_manager
        self.previous_tickers : dict[datetime, TickerResponse] = {}
    
    @property
    def simulation_warmup_steps(self):
        return 0

    def observation_space(self) -> Space:
        return Dict(spaces = {
            "ticker_open" : Box(low= 0, high = np.inf, dtype = float),
            "ticker_high" : Box(low= 0, high = np.inf, dtype = float),
            "ticker_low" : Box(low= 0, high = np.inf, dtype = float),
            "ticker_close" : Box(low= 0, high = np.inf, dtype = float),
            "ticker_volume" : Box(low= 0, high = np.inf, dtype = float)
        })

    async def get_obs(self, date : datetime = None):
        if date is None: date = await self.time_manager.get_current_datetime()
        ticker = await self.exchange_manager.get_ticker(pair = self.pair, date = date)
        return {
            "ticker_open" : float(ticker.open.amount),
            "ticker_high" : float(ticker.high.amount),
            "ticker_low" : float(ticker.low.amount),
            "ticker_close" : float(ticker.close.amount),
            "ticker_volume" : float(ticker.volume.amount)
        }





