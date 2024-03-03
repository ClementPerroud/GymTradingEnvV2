from core import Asset
from .reward import AbstractReward
from exchanges import AbstractExchange
from utils.analyser import PortfolioAnalyser
from math import log

class PerformanceReward(AbstractReward):
    @classmethod
    async def create(cls, exchange : AbstractExchange, quote_asset = Asset) -> None:
        self = cls()
        self.exchange = exchange
        self.quote_asset = quote_asset
        self.portfolio_analyser = await PortfolioAnalyser.create(exchange=exchange, quote_asset=quote_asset)
        await self.reset()
        return self

    async def reset(self):
        self.last_valuation = await self.__compute_valuation()

    async def __compute_valuation(self):
        current_portfolio = await self.exchange.get_portfolio()
        return await self.portfolio_analyser.valuation(
            portfolio= current_portfolio
        )
    async def get(self):
        # Compute requirements
        current_valuation = await self.__compute_valuation()
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
        # Update history
        self.last_valuation = current_valuation
        self.last_portfolio = await self.exchange.get_portfolio()
        return reward