from math import log
from datetime import datetime
import asyncio

from ..core import Asset, Portfolio
from .reward import AbstractReward
from ..exchanges import AbstractExchange
from ..managers.analyser import PortfolioManager
from ..time_managers import AbstractTimeManager

class PerformanceReward(AbstractReward):
    def __init__(self, initial_portfolio :Portfolio, quote_asset = Asset) -> None:
        self.initial_portfolio = initial_portfolio
        self.quote_asset = quote_asset
        self.portfolio_manager = PortfolioManager(quote_asset=self.quote_asset)
    
    async def reset(self, date : datetime, seed = None):
        self.exchange  = self.get_trading_env().exchange
        self.time_manager = self.get_trading_env().time_manager
        self.last_valuation = await self.__compute_valuation(portfolio= self.initial_portfolio, date= date)

    async def __compute_valuation(self, portfolio : Portfolio, date : datetime = None):
        return await self.portfolio_manager.valuation(
            portfolio= portfolio, date= date
        )

    async def compute_reward(self):
        # Compute requirements
        async with asyncio.TaskGroup() as tg:
            current_portfolio = tg.create_task(self.exchange.get_portfolio())
            current_datetime = tg.create_task(self.time_manager.get_current_datetime())

        current_valuation = await self.__compute_valuation(
            portfolio= current_portfolio.result(),
            date= current_datetime.result()
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