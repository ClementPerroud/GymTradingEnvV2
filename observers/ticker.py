from gymnasium.spaces import Space, Box
import numpy as np
from datetime import datetime, timedelta
import asyncio

from ..exchanges import AbstractExchange
from ..exchanges.responses import TickerResponse
from ..time_managers import AbstractTimeManager
from ..core import Pair

from .observer import AbstractObserver

class TickerObserver(AbstractObserver):
    def __init__(self, pair : Pair) -> None:
        super().__init__()

        self.pair = pair

    async def reset(self, date : datetime, seed = None) -> None:
        self.time_manager = self.get_trading_env().time_manager
        self.exchange = self.get_trading_env().exchange
    
    @property
    def simulation_warmup_steps(self):
        return 1

    def observation_space(self) -> Space:
        return Box(shape = (3,), high = np.inf, low = - np.inf)

    async def get_obs(self, date : datetime = None):
        if date is None: date = await self.time_manager.get_current_datetime()

        ticker : TickerResponse  = await self.exchange.get_ticker(pair = self.pair, date= date)
        previous_ticker_date_close = await self.time_manager.get_historical_datetime(step_back= 1, relative_date= date)
        previous_ticker : TickerResponse  = await self.exchange.get_ticker(pair = self.pair, date= previous_ticker_date_close)
        return self.__get_obs_from_tickers(ticker= ticker, previous_ticker= previous_ticker)

    def __get_obs_from_tickers(self, ticker : TickerResponse, previous_ticker : TickerResponse):
        high_feature = ticker.high / ticker.open - 1
        low_feature = ticker.low / ticker.open - 1
        close_feature = ticker.close / previous_ticker.close - 1
        result =  [
            float(high_feature), 
            float(low_feature), 
            float(close_feature)
        ]
        return result