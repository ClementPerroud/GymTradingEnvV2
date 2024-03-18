from functools import lru_cache
from decimal import Decimal
import asyncio
from datetime import datetime

from exchanges import AbstractExchange
from core import Portfolio, PortfolioExposition, Pair, Asset, Value
from utils.singleton import SingletonOnArgs
from .exchange import ExchangeManager

class PositionManager(metaclass = SingletonOnArgs):
    def __init__(self, exchange : AbstractExchange, quote_asset : Asset) -> None:
        self.exchange = exchange
        self.quote_asset = quote_asset
        
    async def valuation(self, position : Value) -> Value:
        if position.asset == self.quote_asset: return position
        return position * await self.exchange.get_quotation(
            pair = Pair(asset= position.asset, quote_asset= self.quote_asset)
        )
    
class PortfolioManager(metaclass = SingletonOnArgs):
    def __init__(self, exchange : AbstractExchange, quote_asset : Asset) -> None:
        self.exchange = exchange
        self.quote_asset = quote_asset
        self.position_manager = PositionManager(exchange= self.exchange, quote_asset= self.quote_asset)

    async def __valuations(self, portfolio : Portfolio) -> dict[Asset, Value]:
        async with asyncio.TaskGroup() as tg:
            asset_valuation_task = {
                position.asset : tg.create_task(self.position_manager.valuation(position))
                    for position in portfolio.get_positions()
            }
        return {
            asset : valuation_task.result()
                for asset, valuation_task in asset_valuation_task.items()
        }
    
    async def valuation(self, portfolio : Portfolio) -> Value:
        _sum = Value(Decimal('0'), self.position_manager.quote_asset)
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


        