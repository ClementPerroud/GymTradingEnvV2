from math import log
from datetime import datetime
import asyncio

from ..core import Asset, Portfolio
from .rewarder import AbstractRewarder
from ..exchanges import AbstractExchange
from ..managers.portfolio import PortfolioManager
from ..time_managers import AbstractTimeManager

class PerformanceRewarder(AbstractRewarder):
    def __init__(self, quote_asset : Asset, multiply_by = 800) -> None:
        super().__init__(multiply_by= multiply_by)
        self.quote_asset = quote_asset
        self.portfolio_manager = PortfolioManager(quote_asset=self.quote_asset)
    
    async def reset(self, seed = None):
        self.exchange_manager  = self.get_trading_env().exchange_manager
        self.time_manager = self.get_trading_env().time_manager
        
        portfolio = await self.exchange_manager.get_portfolio()
        self.last_valuation = await self.__compute_valuation(portfolio= portfolio, date= await self.time_manager.get_current_datetime())

    async def __compute_valuation(self, portfolio : Portfolio, date : datetime = None):
        return await self.portfolio_manager.valuation(
            portfolio= portfolio, date= date
        )

    async def compute_reward(self):
        # Compute requirements
        
        current_portfolio, current_datetime = await self.gather(
            self.exchange_manager.get_portfolio(),
            self.time_manager.get_current_datetime() 
        )

        current_valuation = await self.__compute_valuation(
            portfolio= current_portfolio,
            date= current_datetime
        )

        # Compute rewards
        try:
            reward = log(current_valuation / self.last_valuation)
        except ValueError as e:
            raise ValueError(
                """Cannot compute the PerformanceReward on a zero valuation Portfolio.
                This situation can happen when the valuation come really close to zero 
                and pass bellow tolerance threeshold of the Decimal module. I 
                recommend adding a ValuationEnder to your environment to avoid
                this situation. You can also adjust tolerance with
                the getcontext().prec = ... from module Decimal."""
            )
        self.last_valuation = current_valuation
        return reward