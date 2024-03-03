from exchanges import AbstractExchange
from utils.analyser import PortfolioAnalyser
from core import Value

from .ender import AbstractEnder

class ValuationEnder(AbstractEnder):
    @classmethod
    async def create(cls,
            valuation_threeshold : Value,
            exchange : AbstractExchange
        ) -> None:
        self = cls()
        self.valuation_threeshold = valuation_threeshold
        self.exchange = exchange
        self.quote_asset = valuation_threeshold.asset
        
        self.portfolio_analyser = await PortfolioAnalyser.create(
            exchange= exchange,
            quote_asset= self.quote_asset
        )
        return self 
    
    async def check(self) -> tuple[bool, bool]:
        portfolio = await self.exchange.get_portfolio()
        valuation = await self.portfolio_analyser.valuation(portfolio = portfolio)
        terminated = valuation <= self.valuation_threeshold
        truncated = False
        return terminated, truncated