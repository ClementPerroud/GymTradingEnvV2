from gymnasium.spaces import Space, Box, Dict
import numpy as np
from datetime import datetime

from ..managers import PortfolioManager
from ..core import Pair, PortfolioExposition, Portfolio, Value

from .observer import AbstractObserver

class ExpositionObserver(AbstractObserver):
    def __init__(self, pairs : list[Pair], quote_asset : Pair, **kwargs) -> None:
        super().__init__(**kwargs)
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
        return Dict(spaces = {
            f"exposition_{i}" : Box(high = np.inf, low = - np.inf)   for i, pair in enumerate(self.pairs)
        })
    
    async def get_obs(self, date : datetime = None):
        portfolio = await self.exchange_manager.get_portfolio()
        exposition = await self.portfolio_manager.exposition(portfolio= portfolio, date= date)
        result = {}
        for i, pair in enumerate(self.pairs):
            pair_exposition = exposition.get_position(asset = pair.asset)
            if pair_exposition is None: pair_exposition = 0
            else: pair_exposition = float(pair_exposition.amount)

            result[f"exposition_{i}"] = pair_exposition 

        return result
    
    # async def transform(self, obs):
    #     return 
    

