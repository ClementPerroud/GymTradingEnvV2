from gymnasium.spaces import Space, Box
import numpy as np
import asyncio

from exchanges import AbstractExchange
from exchanges.responses import TickerResponse
from time_managers import AbstractTimeManager
from core import Pair

from .observer import AbstractObserver

class TickerObserver(AbstractObserver):
    observation_lookback = 1
    def __init__(self, pair : Pair, exchange : AbstractExchange, time_manager :  AbstractTimeManager) -> None:
        super().__init__()
        self.exchange = exchange
        self.time_manager = time_manager
        self.pair = pair
        self.observation_lookback = 2

    def observation_space(self) -> Space:
        return Box(shape = (3,), high = np.inf, low = - np.inf)
    
    async def get_obs(self):
        previous_ticker_date_close = await self.time_manager.get_historical_datetime(step_back= 1)

        ticker : TickerResponse  = await self.exchange.get_ticker(self.pair)
        previous_ticker : TickerResponse  = await self.exchange.get_ticker_at_date(pair = self.pair, date_close= previous_ticker_date_close)

        high_feature = ticker.high / ticker.open
        low_feature = ticker.low / ticker.open
        close_feature = ticker.close / previous_ticker.close
        result =  [high_feature, low_feature, close_feature]
        return result