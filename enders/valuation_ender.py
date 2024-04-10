from datetime import datetime
from typing import Tuple

from ..exchanges import AbstractExchange
from ..managers.portfolio import PortfolioManager
from ..core import Value

from .ender import AbstractEnder

class ValuationEnder(AbstractEnder):
    def __init__(self,
            valuation_threeshold : Value,
        ) -> None:
        self.valuation_threeshold = valuation_threeshold
        self.quote_asset = valuation_threeshold.asset
        self.portfolio_manager = PortfolioManager(quote_asset= self.quote_asset)

    async def reset(self, seed = None):
        self.exchange_manager = self.get_trading_env().exchange_manager

    
    async def check(self) -> Tuple[bool, bool]:
        portfolio = await self.exchange_manager.get_portfolio()
        valuation = await self.portfolio_manager.valuation(portfolio = portfolio)
        terminated = valuation <= self.valuation_threeshold

        truncated = False
        return terminated, truncated, True