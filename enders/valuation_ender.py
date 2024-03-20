from ..exchanges import AbstractExchange
from ..managers.analyser import PortfolioManager
from ..core import Value

from .ender import AbstractEnder

class ValuationEnder(AbstractEnder):
    def __init__(self,
            valuation_threeshold : Value,
            exchange : AbstractExchange
        ) -> None:
        self.valuation_threeshold = valuation_threeshold
        self.exchange = exchange
        self.quote_asset = valuation_threeshold.asset
        
        self.portfolio_manager = PortfolioManager(
            exchange= exchange,
            quote_asset= self.quote_asset
        )
    
    async def check(self) -> tuple[bool, bool]:
        portfolio = await self.exchange.get_portfolio()
        valuation = await self.portfolio_manager.valuation(portfolio = portfolio)
        terminated = valuation <= self.valuation_threeshold
        truncated = False
        return terminated, truncated