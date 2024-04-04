from math import log
from datetime import datetime
import asyncio

from ..core import Asset, Portfolio
from .reward import AbstractReward
from ..exchanges import AbstractExchange
from ..managers.portfolio import PortfolioManager
from ..time_managers import AbstractTimeManager

class DifferentialSharpeRatioReward(AbstractReward):
    def __init__(self, eta, initial_portfolio :Portfolio, quote_asset : Asset, multiply_by = 800) -> None:
        super().__init__(multiply_by= multiply_by)
        self.eta = eta
        self.initial_portfolio = initial_portfolio
        self.quote_asset = quote_asset
        self.portfolio_manager = PortfolioManager(quote_asset=self.quote_asset)
    
    async def reset(self, date : datetime, seed = None):
        self.exchange_manager  = self.get_trading_env().exchange_manager
        self.time_manager = self.get_trading_env().time_manager
        self.last_valuation = await self.__compute_valuation(portfolio= self.initial_portfolio, date= date)
        self.A_last = 0
        self.B_last = 0

    async def __compute_valuation(self, portfolio : Portfolio, date : datetime = None):
        return await self.portfolio_manager.valuation(
            portfolio= portfolio, date= date
        )

    async def compute_reward(self):
        # Compute requirements
        
        current_portfolio, current_datetime = await asyncio.gather(
            self.exchange_manager.get_portfolio(),
            self.time_manager.get_current_datetime() 
        )

        current_valuation = await self.__compute_valuation(
            portfolio= current_portfolio,
            date= current_datetime
        )

        R_current = current_valuation / self.last_valuation - 1

        self.A_current = self.eta * R_current + (1 - self.eta) * self.A_last
        self.B_current = self.eta * (R_current**2) + (1 - self.eta) * self.B_last
        delta_A = R_current - self.A_last
        delta_B = R_current ** 2 - self.B_last
        reward = (
            (self.B_last * delta_A - self.A_last * delta_B * 0.5) 
            / (self.B_last - self.A_last**2)**(3/2)
        )

        # Update for next reward
        self.A_last = self.A_current
        self.B_last = self.B_current
        self.last_valuation = current_valuation
        return reward