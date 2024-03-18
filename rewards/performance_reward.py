from core import Asset
from .reward import AbstractReward
from exchanges import AbstractExchange
from managers.analyser import PortfolioManager
from math import log

class PerformanceReward(AbstractReward):
    def __init__(self, exchange : AbstractExchange, quote_asset = Asset) -> None:
        self.exchange = exchange
        self.quote_asset = quote_asset
        self.portfolio_manager = PortfolioManager(exchange=exchange, quote_asset=quote_asset)


    async def reset(self, date):
        self.last_valuation = await self.__compute_valuation()

    async def __compute_valuation(self):
        current_portfolio = await self.exchange.get_portfolio()
        return await self.portfolio_manager.valuation(
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