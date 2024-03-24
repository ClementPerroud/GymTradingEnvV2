from functools import lru_cache
from decimal import Decimal
import asyncio
from datetime import datetime

from ..exchanges import AbstractExchange
from ..element import AbstractEnvironmentElement
from ..core import Portfolio, PortfolioExposition, Pair, Asset, Value
from .exchange import ExchangeManager

class PositionManager(AbstractEnvironmentElement):
    def __init__(self,  quote_asset : Asset) -> None:
        self.quote_asset = quote_asset

    async def reset(self, date : datetime, seed = None):
        self.exchange = self.get_trading_env().exchange

    async def valuation(self, position : Value, date : datetime = None) -> Value:
        if position.asset == self.quote_asset: return position
        return position * await self.exchange.get_quotation(
            pair = Pair(asset= position.asset, quote_asset= self.quote_asset),
            date= date
        )
    
class PortfolioManager(AbstractEnvironmentElement):
    def __init__(self, quote_asset : Asset) -> None:
        self.quote_asset = quote_asset
        self.position_manager = PositionManager(quote_asset= self.quote_asset)

    async def reset(self, date : datetime, seed = None):
        self.exchange = self.get_trading_env().exchange

    async def __valuations(self, portfolio : Portfolio, date : datetime = None) -> dict[Asset, Value]:
        async with asyncio.TaskGroup() as tg:
            asset_valuation_task = {
                position.asset : tg.create_task(self.position_manager.valuation(position = position, date= date))
                    for position in portfolio.get_positions()
            }
        return {
            asset : valuation_task.result()
                for asset, valuation_task in asset_valuation_task.items()
        }
    
    async def valuation(self, portfolio : Portfolio, date : datetime = None) -> Value:
        _sum = Value(Decimal('0'), self.position_manager.quote_asset)
        for value in (await self.__valuations(portfolio = portfolio, date= date)).values():
            _sum += value
        return _sum
    
    async def exposition(self, portfolio : Portfolio, date : datetime = None):
        async with asyncio.TaskGroup() as tg:
            valuations_task = tg.create_task(self.__valuations(portfolio= portfolio, date=date))
            total_valation_task = tg.create_task(self.valuation(portfolio = portfolio, date=date))
            
        total_valation = total_valation_task.result()
        return PortfolioExposition(
            expositions = {
                asset : valuation / total_valation
                for asset, valuation in valuations_task.result().items() 
            }
        )


        