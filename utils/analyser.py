from functools import lru_cache
from decimal import Decimal
import asyncio

from exchanges import AbstractExchange
from core import Portfolio, PortfolioExposition, Pair, Asset, Value
from utils.singleton import SingletonOnArgs
from .exchange_manager import ExchangeManager

class PositionAnalyser(metaclass = SingletonOnArgs):
    @classmethod
    async def create(cls, exchange : AbstractExchange, quote_asset : Asset) -> None:
        self = cls()
        self.exchange = exchange
        self.quote_asset = quote_asset
        self.exchange_manager = await ExchangeManager.create(exchange= self.exchange)
        return self

    
    async def valuation(self, position : Value) -> Value:
        if position.asset == self.quote_asset: return position
        return position * await self.exchange.get_quotation(
            pair = Pair(asset= position.asset, quote_asset= self.quote_asset)
        )
    
class PortfolioAnalyser(metaclass = SingletonOnArgs):
    @classmethod
    async def create(cls, exchange : AbstractExchange, quote_asset : Asset) -> None:
        self = cls()
        self.exchange = exchange
        self.quote_asset = quote_asset
        self.position_analyser = await PositionAnalyser.create(exchange= self.exchange, quote_asset= self.quote_asset)
        return self

    async def __valuations(self, portfolio : Portfolio) -> dict[Asset, Value]:
        async with asyncio.TaskGroup() as tg:
            asset_valuation_task = {
                position.asset : tg.create_task(self.position_analyser.valuation(position))
                    for position in portfolio.get_positions()
            }
        return {
            asset : valuation_task.result()
                for asset, valuation_task in asset_valuation_task.items()
        }
    
    async def valuation(self, portfolio : Portfolio) -> Value:
        _sum = Value(Decimal('0'), self.position_analyser.quote_asset)
        for value in (await self.__valuations(portfolio = portfolio)).values():
            _sum += value
        return _sum
    
    async def exposition(self, portfolio : Portfolio):
        async with asyncio.TaskGroup() as tg:
            valuations_task = tg.create_task(self.__valuations(portfolio= portfolio))
            total_valation_task = tg.create_task(self.valuation(portfolio = portfolio))
            
        total_valation = total_valation_task.result()
        return PortfolioExposition(
            expositions = {
                asset : valuation / total_valation
                for asset, valuation in valuations_task.result().items() 
            }
        )


        