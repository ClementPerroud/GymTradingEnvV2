from gymnasium.spaces import Space, Box
import numpy as np
from datetime import datetime
from typing import List

from ..managers import PortfolioManager
from ..core import Pair, PortfolioExposition, Portfolio, Value

from .observer import AbstractObserver

class ExpositionObserver(AbstractObserver):
    def __init__(self, pairs : List[Pair], quote_asset : Pair) -> None:
        super().__init__()
        self.pairs = pairs
        self.quote_asset = quote_asset
        self.portfolio_manager = PortfolioManager(quote_asset=self.quote_asset)

    async def reset(self, seed = None) -> None:
        self.time_manager = self.get_trading_env().time_manager
        self.exchange_manager = self.get_trading_env().exchange_manager
    
    @property
    def simulation_warmup_steps(self):
        return 1

    def observation_space(self) -> Space:
        return Box(shape = (len(self.pairs),), high = np.inf, low = - np.inf)
    
    async def get_obs(self, date : datetime = None):
        portfolio = await self.exchange_manager.get_portfolio()
        exposition = await self.portfolio_manager.exposition(portfolio= portfolio, date= date)
        results = [exposition.get_position(asset = pair.asset) for pair in self.pairs]
        for index, value in enumerate(results):
            if value is None:
                results[index] = 0
            elif isinstance(value, Value):
                results[index] = float(value.amount)

        return results
    

