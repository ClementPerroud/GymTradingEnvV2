from datetime import datetime
from typing import Tuple

from ..exchanges import AbstractExchange
from ..managers.portfolio import PortfolioManager
from ..core import Value

from .checker import AbstractChecker

class ValuationChecker(AbstractChecker):
    def __init__(self,
            valuation_threeshold : Value,
        ) -> None:
        self.valuation_threeshold = valuation_threeshold
        self.quote_asset = valuation_threeshold.asset

    async def reset(self, seed = None):
        self.exchange_manager = self.get_trading_env().exchange_manager
        self.time_manager = self.get_trading_env().time_manager
        self.portfolio_manager = self.get_trading_env().portfolio_manager

    
    async def check(self) -> Tuple[bool, bool]:
        portfolio = await self.exchange_manager.get_portfolio()
        date = await self.time_manager.get_current_datetime()
        valuation = await self.portfolio_manager.valuation(
            portfolio = portfolio,
            date = date,
            quote_asset= self.quote_asset
        )
        terminated = valuation <= self.valuation_threeshold

        truncated, trainable = False, True
        return terminated, truncated, trainable